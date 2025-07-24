#!/usr/bin/env python3
"""
Azure TTS Avatar Batch Synthesis Implementation
Uses the Azure Batch Avatar API instead of real-time WebRTC
"""

import json
import logging
import time
import os
import sys
import argparse
import requests
from urllib.parse import urlparse

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AzureAvatarBatch:
    def __init__(self, config_file=None):
        self.config = self.load_config(config_file or os.path.expanduser("~/.azure_speech_config"))
        self.avatar_region = self.config.get('AZURE_AVATAR_REGION', 'eastus')
        self.avatar_key = self.config.get('AZURE_AVATAR_KEY', '')
        self.output_dir = "./output/tts"
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        
    def load_config(self, config_file):
        """Load configuration from existing config file"""
        config = {}
        try:
            with open(config_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and '=' in line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        config[key] = value.strip().strip('"\'')
            return config
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {config_file}")
            sys.exit(1)

    def create_batch_synthesis(self, text, voice, avatar):
        """Create a batch synthesis job"""
        # Try the correct Azure TTS Avatar batch API endpoint with API version
        url = f"https://{self.avatar_region}.tts.speech.microsoft.com/avatar/batchsyntheses?api-version=2024-08-01"
        
        headers = {
            'Ocp-Apim-Subscription-Key': self.avatar_key,
            'Content-Type': 'application/json'
        }
        
        # Create SSML with avatar configuration
        ssml = f"""
        <speak version="1.0" xml:lang="en-US">
            <voice name="{voice}">
                <mstts:talkingavatar character="{avatar}" style="graceful-sitting"/>
                {text}
            </voice>
        </speak>
        """
        
        # Batch synthesis request payload
        payload = {
            "displayName": f"Avatar synthesis - {int(time.time())}",
            "description": f"Batch avatar synthesis for {avatar}",
            "textType": "SSML",
            "inputs": [
                {
                    "text": ssml.strip()
                }
            ],
            "properties": {
                "outputFormat": "mp4-720p",
                "talkingAvatarCharacter": avatar,
                "talkingAvatarStyle": "graceful-sitting",
                "backgroundColor": "#FFFFFFFF"
            }
        }
        
        logger.info(f"🚀 Creating batch synthesis job...")
        logger.info(f"Text: {text}")
        logger.info(f"Voice: {voice}")
        logger.info(f"Avatar: {avatar}")
        logger.info(f"API URL: {url}")
        logger.info(f"Payload: {json.dumps(payload, indent=2)}")
        
        try:
            logger.info("📤 Sending request...")
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            logger.info(f"📥 Response status: {response.status_code}")
            logger.info(f"📥 Response headers: {dict(response.headers)}")
            
            if response.status_code == 201:
                job_data = response.json()
                job_id = job_data.get('id')
                logger.info(f"✅ Batch synthesis job created: {job_id}")
                logger.info(f"Job data: {json.dumps(job_data, indent=2)}")
                return job_id
            else:
                logger.error(f"❌ Failed to create batch synthesis job: {response.status_code}")
                logger.error(f"Response body: {response.text}")
                
                # Try to parse error details
                try:
                    error_data = response.json()
                    logger.error(f"Error details: {json.dumps(error_data, indent=2)}")
                except:
                    logger.error("Could not parse error response as JSON")
                
                return None
                
        except requests.exceptions.Timeout:
            logger.error("❌ Request timed out after 30 seconds")
            return None
        except Exception as e:
            logger.error(f"❌ Error creating batch synthesis: {e}")
            return None

    def check_job_status(self, job_id):
        """Check the status of a batch synthesis job"""
        url = f"https://{self.avatar_region}.tts.speech.microsoft.com/avatar/batchsyntheses/{job_id}"
        
        headers = {
            'Ocp-Apim-Subscription-Key': self.avatar_key
        }
        
        try:
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"❌ Failed to check job status: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error checking job status: {e}")
            return None

    def download_result(self, download_url, output_filename):
        """Download the generated avatar video"""
        try:
            logger.info(f"📥 Downloading avatar video...")
            
            response = requests.get(download_url, stream=True)
            
            if response.status_code == 200:
                output_path = os.path.join(self.output_dir, output_filename)
                
                with open(output_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                logger.info(f"✅ Avatar video saved to: {output_path}")
                return output_path
            else:
                logger.error(f"❌ Failed to download result: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error downloading result: {e}")
            return None

    def wait_for_completion(self, job_id, max_wait_time=300):
        """Wait for batch synthesis to complete"""
        start_time = time.time()
        check_interval = 10  # Check every 10 seconds
        
        logger.info(f"⏳ Waiting for synthesis to complete (max {max_wait_time}s)...")
        
        while time.time() - start_time < max_wait_time:
            job_status = self.check_job_status(job_id)
            
            if not job_status:
                logger.error("❌ Failed to check job status")
                return None
            
            status = job_status.get('status', 'Unknown')
            logger.info(f"📊 Job status: {status}")
            
            if status == 'Succeeded':
                logger.info("✅ Synthesis completed successfully!")
                
                # Get the download URL
                outputs = job_status.get('outputs', {})
                result = outputs.get('result')
                
                if result:
                    return result
                else:
                    logger.error("❌ No result URL found in completed job")
                    return None
                    
            elif status == 'Failed':
                logger.error("❌ Synthesis failed")
                error_details = job_status.get('properties', {}).get('error', 'Unknown error')
                logger.error(f"Error details: {error_details}")
                return None
                
            elif status in ['NotStarted', 'Running']:
                logger.info(f"⏳ Synthesis in progress... waiting {check_interval}s")
                time.sleep(check_interval)
            else:
                logger.warning(f"⚠️ Unknown status: {status}")
                time.sleep(check_interval)
        
        logger.error(f"❌ Synthesis timed out after {max_wait_time}s")
        return None

    def synthesize_avatar(self, text, voice="en-US-JennyNeural", avatar="lisa"):
        """Complete avatar synthesis workflow using batch API"""
        logger.info("🎬 Starting Azure TTS Avatar batch synthesis...")
        
        # Step 1: Create batch synthesis job
        job_id = self.create_batch_synthesis(text, voice, avatar)
        if not job_id:
            logger.warning("⚠️ Avatar batch API not available. Falling back to regular TTS...")
            return self.fallback_to_regular_tts(text, voice)
        
        # Step 2: Wait for completion
        result_url = self.wait_for_completion(job_id)
        if not result_url:
            return False
        
        # Step 3: Download the result
        timestamp = int(time.time())
        output_filename = f"avatar_{avatar}_{timestamp}.mp4"
        output_path = self.download_result(result_url, output_filename)
        
        if output_path:
            logger.info("🎉 Avatar synthesis completed successfully!")
            return True
        else:
            logger.error("❌ Failed to download avatar video")
            return False
    
    def fallback_to_regular_tts(self, text, voice):
        """Fallback to regular TTS when avatar API is not available"""
        logger.info("🔄 Using regular TTS as fallback...")
        
        # Get access token for regular TTS
        token_url = f"https://{self.avatar_region}.api.cognitive.microsoft.com/sts/v1.0/issuetoken"
        headers = {'Ocp-Apim-Subscription-Key': self.avatar_key}
        
        try:
            response = requests.post(token_url, headers=headers)
            if response.status_code != 200:
                logger.error(f"❌ Failed to get access token: {response.status_code}")
                return False
            
            access_token = response.text
            
            # Create SSML for regular TTS
            ssml = f"""
            <speak version="1.0" xml:lang="en-US">
                <voice name="{voice}">
                    {text}
                </voice>
            </speak>
            """
            
            # Make TTS request
            tts_url = f"https://{self.avatar_region}.tts.speech.microsoft.com/cognitiveservices/v1"
            tts_headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/ssml+xml',
                'X-Microsoft-OutputFormat': 'riff-24khz-16bit-mono-pcm',
                'User-Agent': 'AzureAvatarFallback'
            }
            
            response = requests.post(tts_url, headers=tts_headers, data=ssml.strip())
            
            if response.status_code == 200:
                timestamp = int(time.time())
                output_filename = f"avatar_fallback_{timestamp}.wav"
                output_path = os.path.join(self.output_dir, output_filename)
                
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                
                logger.info(f"✅ Regular TTS completed successfully!")
                logger.info(f"🎵 Audio saved to: {output_path}")
                logger.info("ℹ️ This is audio-only (no video) since avatar features are not available")
                return True
            else:
                logger.error(f"❌ TTS request failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error in fallback TTS: {e}")
            return False

def main():
    parser = argparse.ArgumentParser(description='Azure TTS Avatar Batch Synthesis')
    parser.add_argument('--text', required=True, help='Text to synthesize')
    parser.add_argument('--voice', default='en-US-JennyNeural', help='Voice to use')
    parser.add_argument('--avatar', default='lisa', help='Avatar character')
    parser.add_argument('--config', help='Config file path')
    
    args = parser.parse_args()
    
    avatar_batch = AzureAvatarBatch(args.config)
    success = avatar_batch.synthesize_avatar(args.text, args.voice, args.avatar)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
