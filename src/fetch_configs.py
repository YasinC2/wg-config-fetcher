import re
import os
import time
import logging
import requests
from bs4 import BeautifulSoup
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

CHANNEL_URLS = [
    "https://t.me/s/freewireguard",
    "https://t.me/s/WireVpnGuard"
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
        
        for channel_url in CHANNEL_URLS:
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
                    
                    # Extract private key from config URL
                    private_key_match = re.search(r'private_key=([a-zA-Z0-9+/=]+)', base_config)
                    if private_key_match:
                        channel_private_keys.append(private_key_match.group(1))
                    
                    if len(channel_configs) >= 10:
                        break  # Stop processing this channel if we have enough configs
            
            # Add this channel's configs to the main list
            configs.extend(channel_configs)
            private_keys.extend(channel_private_keys)
            
            if len(configs) >= 20:
                break  # Stop processing channels if we have enough total configs

        # Take first 20 configs across all channels
        configs = configs[:20]
        
        if not configs:
            logger.error("No WireGuard configs found!")
            return
        
        final_configs = [
            f"{config}#Anon{i+1}"
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
