import re
import os
import time
import logging
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urlparse

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

CHANNEL_TARGETS = [
    ("https://t.me/s/WireVpnGuard", 20),
    ("https://t.me/s/freewireguard", 5)
]
OUTPUT_FILE = 'configs/wireguard_configs.txt'
PRIVATE_KEYS_FILE = 'configs/wireguard_privatekeys.txt'

def fetch_wireguard_configs():
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        configs = []
        private_keys = []
        
        for channel_url, target_count in CHANNEL_TARGETS:
            # Process each channel URL
            response = requests.get(channel_url, headers=headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            messages = soup.find_all('div', class_='tgme_widget_message_text')
            
            channel_configs = []
            channel_private_keys = []
            
            for message in messages:
                if not message.text:
                    continue
                
                matches = re.finditer(r'wireguard://[^\s]+', message.text)
                for match in matches:
                    config = match.group(0)
                    base_config = config.split('#')[0]
                    channel_configs.append(base_config)
                    
                    # Extract private key using URL parsing
                    parsed = urlparse(base_config)
                    if parsed.username:
                        channel_private_keys.append(parsed.username)
                    
                    if len(channel_configs) >= target_count:
                        break  # Stop processing matches if we have enough configs
                
                # Exit message loop if we've reached the per-channel limit
                if len(channel_configs) >= target_count:
                    break
            
            # Add this channel's configs to the main list
            configs.extend(channel_configs)
            private_keys.extend(channel_private_keys)
            

        # Take first 20 configs across all channels
        # configs = configs[:20]
        
        if not configs:
            logger.error("No WireGuard configs found!")
            return
        
        final_configs = [
            f"{config}#WG-{i+1}"
            for i, config in enumerate(configs)
        ]
        
        os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write('\n'.join(final_configs))
        
        with open(PRIVATE_KEYS_FILE, 'w', encoding='utf-8') as f:
            f.write('\n'.join(private_keys))
            
        logger.info(f"Successfully updated configs at {datetime.now()}")

    except Exception as e:
        logger.error(f"Error occurred: {str(e)}")

if __name__ == '__main__':
    fetch_wireguard_configs()
