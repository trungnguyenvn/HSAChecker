#!/usr/bin/env python3
"""
HSA Exam Slot Checker
Enhanced and flexible version with period and batch discovery
Python implementation with support for checking all batches
"""

import argparse
import datetime
import json
import os
import platform
import subprocess
import sys
import time
from typing import Dict, List, Optional, Tuple, Union

import requests

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="HSA Exam Slot Checker")
    parser.add_argument("-b", "--batch-code", help="Check specific batch by code (e.g. 502, 503)")
    parser.add_argument("-l", "--location-id", help="Only check a specific location ID")
    parser.add_argument("-i", "--interval", type=int, default=300, 
                      help="Interval in seconds between checks when monitoring (default: 300)")
    parser.add_argument("-d", "--delay", type=int, default=2,
                      help="Delay in seconds between API calls (default: 2)")
    parser.add_argument("-e", "--email", default="your-email-address",
                      help="Email to send notifications to")
    parser.add_argument("-n", "--no-email", action="store_true",
                      help="No email notifications, just display results")
    parser.add_argument("-v", "--verbose", action="store_true",
                      help="Verbose output (show progress for each location)")
    parser.add_argument("-m", "--monitor", action="store_true",
                      help="Monitor mode - continuously check at specified intervals")
    parser.add_argument("-p", "--phone", help="Phone number for authentication")
    parser.add_argument("-w", "--password", help="Password for authentication")
    parser.add_argument("-t", "--token", help="Custom authorization token")
    parser.add_argument("-a", "--show-batches", action="store_true",
                      help="Show all available batches and exit")
    parser.add_argument("--all-batches", action="store_true",
                      help="Check all OPENING batches instead of just one")
    parser.add_argument("--status", default="OPENING", 
                      help="Status of batches to check (default: OPENING)")

    return parser.parse_args()

class HSAChecker:
    """HSA Exam Slot Checker class"""
    
    def __init__(self, args):
        """Initialize the checker with arguments"""
        self.batch_code = args.batch_code
        self.location_id = args.location_id
        self.from_email = "validated-email"
        self.to_email = args.email
        self.interval = args.interval
        self.delay = args.delay
        self.no_email = args.no_email
        self.verbose = args.verbose
        self.monitor_mode = args.monitor
        self.phone = args.phone
        self.password = args.password
        self.token = args.token
        self.show_batches_only = args.show_batches
        self.check_all_batches = args.all_batches
        self.batch_status = args.status
        
        # Variables that will be set later
        self.period_id = None
        self.batch_id = None
        self.batch_name = None
        self.batch_code = None
        self.results_file = f"results-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}.tmp"
        self.available_found = False
        
        # Setup headers
        self.base_headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9,vi;q=0.8",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "DNT": "1",
            "Origin": "https://id.hsa.edu.vn",
            "Pragma": "no-cache",
            "Referer": "https://id.hsa.edu.vn/",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
        }
        
        # Authenticate if needed
        if not self.token and self.phone and self.password:
            self.authenticate()
            
        if self.token:
            self.headers = {**self.base_headers, "Authorization": f"Bearer {self.token}"}
        else:
            print("Error: No authentication token available. Please provide either a token with -t or phone/password with -p/-w")
            sys.exit(1)
    
    def authenticate(self) -> bool:
        """Authenticate and get a token"""
        print(f"Authenticating with phone number {self.phone}...")
        
        auth_data = {"id": self.phone, "password": self.password}
        
        try:
            response = requests.post(
                'https://api.hsa.edu.vn/accounts/sign-in',
                headers=self.base_headers,
                json=auth_data
            )
            response.raise_for_status()
            
            auth_data = response.json()
            self.token = auth_data.get('token')
            
            if not self.token:
                print("Authentication failed. Check your phone number and password.")
                print(f"Response: {response.text}")
                return False
            
            print("Authentication successful!")
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"Authentication failed: {str(e)}")
            return False
        finally:
            time.sleep(self.delay)
    
    def api_call(self, url: str, method: str = 'GET', data: dict = None) -> dict:
        """Safely make an API call with delay"""
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=self.headers)
            else:  # POST
                response = requests.post(url, headers=self.headers, json=data)
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"API call failed: {str(e)}")
            return {}
        finally:
            time.sleep(self.delay)
    
    def fetch_periods(self) -> list:
        """Fetch available exam periods"""
        return self.api_call("https://api.hsa.edu.vn/exam/views/registration/available-period")
    
    def fetch_batches(self, period_id: str) -> list:
        """Fetch batches for a period"""
        return self.api_call(f"https://api.hsa.edu.vn/exam/views/registration/available-batch?periodId={period_id}")
    
    def fetch_locations(self, batch_id: str) -> list:
        """Fetch locations for a batch"""
        return self.api_call(f"https://api.hsa.edu.vn/exam/views/registration/available-location?batchId={batch_id}")
    
    def play_notification_sound(self):
        """Play notification sound based on platform"""
        try:
            system = platform.system()
            if system == "Darwin":  # macOS
                subprocess.Popen(['afplay', '/System/Library/Sounds/Submarine.aiff'])
            elif system == "Linux":
                if os.path.exists("/usr/bin/paplay"):
                    subprocess.Popen(['paplay', '/usr/share/sounds/freedesktop/stereo/complete.oga'])
                elif os.path.exists("/usr/bin/aplay"):
                    subprocess.Popen(['aplay', '/usr/share/sounds/sound-icons/prompt.wav'])
            elif system == "Windows":
                subprocess.Popen(['powershell.exe', '-c', "(New-Object Media.SoundPlayer 'C:\\Windows\\Media\\notify.wav').PlaySync();"])
        except Exception as e:
            print(f"Failed to play notification sound: {str(e)}")
    
    def send_email_notification(self, batch_name=None, batch_code=None):
        """Send an email notification"""
        if self.no_email:
            print(f"{self._timestamp()} Email notifications disabled.")
            return True
        
        try:
            import boto3
            from botocore.exceptions import ClientError
            
            subject = "HSA Exam Slots Available!"
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Use provided batch details or instance variables
            batch_name = batch_name or self.batch_name
            batch_code = batch_code or self.batch_code
            
            # Read available slots from the results file
            available_slots = []
            with open(self.results_file, 'r') as f:
                for line in f:
                    if "✓" in line and "has" in line and "available" in line:
                        available_slots.append(line.strip())
            
            # Create a simplified summary for the email
            text_content = f"HSA Exam Slots Available as of {timestamp}\n\n"
            
            if batch_name and batch_code:
                text_content += f"Batch: {batch_name} (Code: {batch_code})\n\n"
            else:
                text_content += "Multiple batches have available slots\n\n"
                
            text_content += "Available slots summary:\n"
            for slot in available_slots:
                text_content += f"{slot.split(' ', 1)[1]}\n"  # Remove timestamp
            text_content += "\n\nCheck https://id.hsa.edu.vn to register now."
            
            # Create HTML version
            html_content = "<html><body>"
            html_content += f"<h1>HSA Exam Slots Available!</h1>"
            html_content += f"<p>As of {timestamp}, the following locations have available slots:</p>"
            
            if batch_name and batch_code:
                html_content += f"<p><strong>Batch:</strong> {batch_name} (Code: {batch_code})</p>"
            else:
                html_content += "<p><strong>Multiple batches have available slots</strong></p>"
                
            html_content += "<ul>"
            
            for slot in available_slots:
                parts = slot.split(" ✓ ", 1)
                if len(parts) > 1:
                    slot_info = parts[1]
                    location_info = slot_info.split(" (ID: ")
                    if len(location_info) > 1:
                        location = location_info[0]
                        id_and_slots = location_info[1].split(") has ")
                        if len(id_and_slots) > 1:
                            location_id = id_and_slots[0]
                            slots = id_and_slots[1].replace(" available", "")
                            html_content += f"<li><strong>{location}</strong> (ID: {location_id}): {slots} available sessions</li>"
            
            html_content += "</ul>"
            html_content += "<p>Visit <a href='https://id.hsa.edu.vn'>id.hsa.edu.vn</a> to register now!</p>"
            html_content += "</body></html>"
            
            # Configure email
            client = boto3.client('ses', region_name='us-east-1')
            
            message = {
                'Subject': {'Data': subject, 'Charset': 'UTF-8'},
                'Body': {
                    'Text': {'Data': text_content, 'Charset': 'UTF-8'},
                    'Html': {'Data': html_content, 'Charset': 'UTF-8'}
                }
            }
            
            client.send_email(
                Source=self.from_email,
                Destination={'ToAddresses': [self.to_email]},
                Message=message
            )
            
            print(f"{self._timestamp()} Email notification sent to {self.to_email}")
            return True
            
        except ImportError:
            print(f"{self._timestamp()} Warning: boto3 not installed. Email not sent.")
            print("Install boto3 with: pip install boto3")
            return False
        except Exception as e:
            print(f"{self._timestamp()} Failed to send email: {str(e)}")
            return False
    
    def check_slots(self, location_id: str, location_name: str, batch_name: str = None, batch_code: str = None) -> bool:
        """Check available slots for a location"""
        response = self.api_call(f"https://api.hsa.edu.vn/exam/views/registration/available-slot?locationId={location_id}")
        
        if not response:
            self._log(f"× Failed to fetch slots for {location_name} (ID: {location_id})")
            return False
        
        # Get count of available slots
        available_count = 0
        available_slots = []
        
        for slot in response:
            # Convert ID to string to ensure compatibility
            slot_id = str(slot.get('id'))
            name = slot.get('name')
            total = int(slot.get('numberOfSeats', 0))
            registered = int(slot.get('registeredSlots', 0))
            available = total - registered
            
            if available > 0:
                available_count += 1
                batch_prefix = f"[{batch_code}] " if batch_code else ""
                slot_info = f"{self._timestamp()} → {batch_prefix}{name} (ID: {slot_id}): {available}/{total}"
                available_slots.append(slot_info)
        
        # Display results
        batch_info = f" for {batch_name} (Code: {batch_code})" if batch_name and batch_code else ""
        
        if available_count == 0:
            if self.verbose:
                self._log(f"× No available slots at {location_name} (ID: {location_id}){batch_info}")
            else:
                self._log_file(f"× No available slots at {location_name} (ID: {location_id}){batch_info}")
        else:
            self._log(f"✓ {location_name} (ID: {location_id}){batch_info} has {available_count} available session(s):")
            for slot in available_slots:
                self._log(slot)
            return True
        
        return False
    
    def run_check_for_batch(self, batch_id, batch_name, batch_code):
        """Run a check for a specific batch"""
        self._log(f"Starting check for Batch: {batch_name} (Code: {batch_code}, ID: {batch_id})")
        self._log("-------------------------------------------------------------------")
        
        # If specific location ID is provided
        if self.location_id:
            self._log(f"Checking specific location ID: {self.location_id}")
            
            # Fetch the location name first
            locations_response = self.fetch_locations(batch_id)
            
            location_name = "Unknown Location"
            for loc in locations_response:
                if str(loc.get('id')) == str(self.location_id):
                    location_name = loc.get('name')
                    break
            
            # Check slots for this location
            locations_with_slots = 1 if self.check_slots(self.location_id, location_name, batch_name, batch_code) else 0
        else:
            # Fetch all locations
            locations_response = self.fetch_locations(batch_id)
            
            if not locations_response:
                self._log(f"Error: Failed to fetch locations for batch {batch_code} or empty response")
                return False
            
            # Process each location
            location_count = 0
            locations_with_slots = 0
            
            self._log(f"Processing all locations in batch {batch_code}...")
            
            total_locations = len(locations_response)
            
            for location in locations_response:
                location_id = location.get('id')
                location_name = location.get('name')
                location_count += 1
                
                # Show progress
                if self.verbose:
                    print(f"\rChecking location {location_count}/{total_locations}: {location_name}...", end="", flush=True)
                else:
                    print(f"\rChecking location {location_count}/{total_locations}...", end="", flush=True)
                
                # Check slots
                if self.check_slots(location_id, location_name, batch_name, batch_code):
                    locations_with_slots += 1
            
            # Clear progress line
            print("\r" + " " * 80 + "\r", end="", flush=True)
            
            # Display batch summary
            self._log(f"--------------------------------------------------------------------")
            self._log(f"Batch: {batch_name} (Code: {batch_code})")
            self._log(f"Total locations checked: {location_count}")
            self._log(f"Locations with available slots: {locations_with_slots}")
            self._log("--------------------------------------------------------------------")
        
        # Return if slots were found
        return locations_with_slots > 0
    
    def run_check(self):
        """Run checks across all selected batches"""
        self._log("===================================================================")
        self._log("STARTING SLOT CHECK")
        self._log("===================================================================")
        
        if self.check_all_batches:
            # Get all matching batches
            batches_response = self.fetch_batches(self.period_id)
            matching_batches = [b for b in batches_response if b.get('status') == self.batch_status]
            
            if not matching_batches:
                self._log(f"No batches with status '{self.batch_status}' found.")
                return False
            
            self._log(f"Checking {len(matching_batches)} batches with status '{self.batch_status}'")
            
            # Track overall results
            total_batches_checked = 0
            batches_with_slots = 0
            self.available_found = False
            
            # Check each batch
            for batch in matching_batches:
                batch_id = batch.get('id')
                batch_name = batch.get('name')
                batch_code = batch.get('code')
                
                total_batches_checked += 1
                
                # Run check for this batch
                if self.run_check_for_batch(batch_id, batch_name, batch_code):
                    batches_with_slots += 1
                    self.available_found = True
                
                # Add a separator between batches
                self._log("-------------------------------------------------------------------")
            
            # Display final results
            self._log("====================================================================")
            self._log("OVERALL RESULTS SUMMARY:")
            self._log("====================================================================")
            self._log(f"Total batches checked: {total_batches_checked}")
            self._log(f"Batches with available slots: {batches_with_slots}")
            self._log("--------------------------------------------------------------------")
            
            # Notify if slots found in any batch
            if self.available_found:
                if not self.no_email:
                    self.send_email_notification(batch_name=None, batch_code=None)  # Send with no specific batch
                self.play_notification_sound()
            else:
                self._log("No available slots found in any batch.")
            
        else:
            # Use the single batch we've already identified
            self.available_found = self.run_check_for_batch(self.batch_id, self.batch_name, self.batch_code)
            
            # Show results and send notification if slots are available
            if self.available_found:
                if not self.no_email:
                    self.send_email_notification()
                self.play_notification_sound()
            else:
                self._log("No available slots found.")
        
        self._log("====================================================================")
        self._log(f"Check completed at {datetime.datetime.now()}")
        
        return self.available_found
    
    def display_batches(self, period_id: str, batches: list):
        """Display available batches"""
        print("=====================================================================")
        print("AVAILABLE BATCHES:")
        print("=====================================================================")
        
        for batch in batches:
            code = batch.get('code', 'N/A')
            batch_id = batch.get('id', 'N/A')
            name = batch.get('name', 'N/A')
            status = batch.get('status', 'N/A')
            
            config = batch.get('config', {})
            start_date = config.get('startDate', 'N/A')
            end_date = config.get('endDate', 'N/A')
            reg_end = config.get('registrationEndDateTime', 'N/A')
            
            print(f"Code: {code} | ID: {batch_id} | Name: {name} | Status: {status} | Start: {start_date} | End: {end_date} | Reg ends: {reg_end}")
        
        print("=====================================================================")
    
    def run(self):
        """Main execution method"""
        print("HSA Exam Slot Checker - Python Version")
        print(f"Using API delay: {self.delay} seconds")
        
        # Fetch available periods first
        print("Fetching available exam periods...")
        periods_response = self.fetch_periods()
        
        if not periods_response:
            print("Error: No active exam periods found.")
            return False
        
        # Extract the first period ID
        self.period_id = periods_response[0].get('id')
        print(f"Found period ID: {self.period_id}")
        
        # Fetch available batches
        batches_response = self.fetch_batches(self.period_id)
        
        # Show all batches and exit if requested
        if self.show_batches_only:
            self.display_batches(self.period_id, batches_response)
            return True
        
        # If not checking all batches, extract specific batch details
        if not self.check_all_batches:
            # Extract batch details
            if self.batch_code:
                # Find specific batch by code
                batch_found = False
                for batch in batches_response:
                    if batch.get('code') == self.batch_code:
                        self.batch_id = batch.get('id')
                        self.batch_name = batch.get('name')
                        batch_status = batch.get('status')
                        batch_found = True
                        break
                        
                if not batch_found:
                    print(f"Error: Batch code '{self.batch_code}' not found.")
                    self.display_batches(self.period_id, batches_response)
                    return False
                    
                if batch_status != "OPENING":
                    print(f"Warning: Batch '{self.batch_name}' (Code: {self.batch_code}) is not in OPENING status. Current status: {batch_status}")
            else:
                # Find first OPENING batch
                opening_batches = [b for b in batches_response if b.get('status') == "OPENING"]
                
                if not opening_batches:
                    print("Error: No OPENING batches found.")
                    self.display_batches(self.period_id, batches_response)
                    return False
                    
                batch = opening_batches[0]
                self.batch_id = batch.get('id')
                self.batch_name = batch.get('name')
                self.batch_code = batch.get('code')
            
            # For debugging - output what we're using
            print(f"Using batch: {self.batch_name} (Code: {self.batch_code}, ID: {self.batch_id}")
        else:
            print("Will check ALL batches with status:", self.batch_status)
        
        # Run once or in monitoring mode
        if self.monitor_mode:
            print(f"Starting monitoring mode. Will check every {self.interval} seconds with {self.delay} seconds delay between API calls.")
            print("Press Ctrl+C to stop.")
            
            run_count = 0
            try:
                while True:
                    run_count += 1
                    print(f"Run #{run_count} at {datetime.datetime.now()}")
                    
                    self.run_check()
                    
                    print(f"Next check in {self.interval} seconds. Press Ctrl+C to stop.")
                    time.sleep(self.interval)
            except KeyboardInterrupt:
                print("\nMonitoring stopped by user.")
                return True
        else:
            self.run_check()
            
            print("To continuously monitor, run with the -m flag")
            print("To check all batches, run with --all-batches")
            print(f"Adjust API delay with -d SECONDS (current: {self.delay})")
            print(f"Set monitoring interval with -i SECONDS (current: {self.interval})")
            print(f"Results saved to {self.results_file}")
            print("To view all available batches, run with the -a flag")
            
            return True
    
    def _timestamp(self) -> str:
        """Return current timestamp in standard format"""
        return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    def _log(self, message: str):
        """Log message to console and file"""
        timestamp = self._timestamp()
        full_message = f"{timestamp} {message}" if not message.startswith(timestamp) else message
        print(full_message)
        self._log_file(full_message)
    
    def _log_file(self, message: str):
        """Log message to file only"""
        with open(self.results_file, 'a') as f:
            f.write(f"{message}\n")

def main():
    """Main entry point"""
    args = parse_arguments()
    checker = HSAChecker(args)
    checker.run()

if __name__ == "__main__":
    main()
