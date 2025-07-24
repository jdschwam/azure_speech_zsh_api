#!/usr/bin/env python3
"""
Azure TTS Avatar WebRTC Implementation
Requires: pip install aiortc aiohttp opencv-python websockets
"""

import asyncio
import json
import logging
import time
import os
import sys
import argparse
import aiohttp
import websockets
from aiortc import RTCPeerConnection, RTCSessionDescription, RTCConfiguration, RTCIceServer
from aiortc.contrib.media import MediaPlayer, MediaRecorder

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AzureAvatarTTS:
    def __init__(self, config_file=None):
        self.config = self.load_config(config_file or os.path.expanduser("~/.azure_speech_config"))
        self.avatar_region = self.config.get('AZURE_AVATAR_REGION', 'eastus')
        self.avatar_key = self.config.get('AZURE_AVATAR_KEY', '')
        self.pc = None
        self.ice_servers = []
        self.recorder = None
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

    async def get_ice_servers(self):
        """Step 1a: Get ICE servers from Azure TTS Avatar API"""
        # Use the correct avatar relay token endpoint
        url = f"https://{self.avatar_region}.tts.speech.microsoft.com/cognitiveservices/avatar/relay/token/v1"
        headers = {
            'Ocp-Apim-Subscription-Key': self.avatar_key
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        # Azure returns ICE server configuration
                        if 'urls' in data and 'username' in data and 'credential' in data:
                            self.ice_servers = [
                                RTCIceServer(
                                    urls=data['urls'],
                                    username=data['username'],
                                    credential=data['credential']
                                )
                            ]
                            logger.info(f"✅ ICE servers retrieved: {len(data['urls'])} servers")
                            return True
                        else:
                            # Try alternative response format
                            urls = data.get('Urls', data.get('iceServers', []))
                            username = data.get('Username', data.get('username', ''))
                            password = data.get('Password', data.get('credential', ''))
                            
                            if urls:
                                self.ice_servers = [
                                    RTCIceServer(
                                        urls=urls,
                                        username=username,
                                        credential=password
                                    )
                                ]
                                logger.info(f"✅ ICE servers retrieved: {len(urls)} servers")
                                return True
                            else:
                                logger.error(f"❌ Unexpected response format: {data}")
                                return False
                    else:
                        logger.error(f"❌ Failed to get ICE servers: {response.status}")
                        error_text = await response.text()
                        logger.error(f"❌ Response: {error_text}")
                        
                        # If the relay endpoint fails, try using standard STUN servers as fallback
                        logger.info("🔄 Falling back to standard STUN servers...")
                        self.ice_servers = [
                            RTCIceServer(urls=["stun:stun.l.google.com:19302"]),
                            RTCIceServer(urls=["stun:stun1.l.google.com:19302"])
                        ]
                        logger.info("✅ Using fallback STUN servers")
                        return True
        except Exception as e:
            logger.error(f"❌ Error getting ICE servers: {e}")
            logger.info("🔄 Falling back to standard STUN servers...")
            self.ice_servers = [
                RTCIceServer(urls=["stun:stun.l.google.com:19302"]),
                RTCIceServer(urls=["stun:stun1.l.google.com:19302"])
            ]
            logger.info("✅ Using fallback STUN servers")
            return True

    async def setup_peer_connection(self):
        """Step 2: Create RTCPeerConnection with ICE servers"""
        if not self.ice_servers:
            success = await self.get_ice_servers()
            if not success:
                return False
        
        # Create peer connection with ICE configuration
        configuration = RTCConfiguration(iceServers=self.ice_servers)
        self.pc = RTCPeerConnection(configuration)
        
        # Set up event handlers
        @self.pc.on("connectionstatechange")
        async def on_connectionstatechange():
            logger.info(f"🔗 Connection state: {self.pc.connectionState}")
        
        @self.pc.on("track")
        def on_track(track):
            logger.info(f"📹 Received track: {track.kind}")
            if track.kind == "video":
                asyncio.create_task(self.setup_video_recorder(track))
        
        logger.info("✅ Peer connection established")
        return True

    async def setup_video_recorder(self, track):
        """Step 5: Capture avatar video output"""
        timestamp = int(time.time())
        output_file = f"{self.output_dir}/avatar_{timestamp}.mp4"
        
        try:
            self.recorder = MediaRecorder(output_file)
            self.recorder.addTrack(track)
            await self.recorder.start()
            logger.info(f"🎥 Started recording avatar video to: {output_file}")
            return output_file
        except Exception as e:
            logger.error(f"❌ Error setting up video recorder: {e}")
            return None

    async def connect_websocket_and_synthesize(self, text, voice, avatar):
        """Steps 3, 4, 5: Connect WebSocket, send config, and stream"""
        # Use the correct Azure TTS Avatar WebSocket endpoint
        ws_url = f"wss://{self.avatar_region}.tts.speech.microsoft.com/cognitiveservices/websocket/v1"
        
        headers = {
            'Ocp-Apim-Subscription-Key': self.avatar_key,
            'X-ConnectionId': f'avatar-{int(time.time())}',
            'Content-Type': 'application/json'
        }
        
        try:
            # Step 3: Connect WebSocket
            async with websockets.connect(ws_url, extra_headers=headers) as websocket:
                logger.info(f"🌐 WebSocket connected to: {ws_url}")
                
                # Step 4: Create and send SDP offer
                offer = await self.pc.createOffer()
                await self.pc.setLocalDescription(offer)
                
                # Send avatar configuration message - using correct Azure format
                config_message = {
                    "context": {
                        "synthesis": {
                            "audio": {
                                "metadataOptions": {
                                    "sentenceBoundaryEnabled": False,
                                    "wordBoundaryEnabled": False
                                },
                                "outputFormat": "audio-24khz-48kbitrate-mono-mp3"
                            },
                            "avatar": {
                                "character": avatar,
                                "style": "graceful-sitting",
                                "background": {
                                    "color": "#FFFFFFFF"
                                }
                            }
                        }
                    }
                }
                
                await websocket.send(json.dumps(config_message))
                logger.info("⚙️ Avatar configuration sent")
                
                # Send SDP offer for WebRTC
                sdp_message = {
                    "type": "offer",
                    "sdp": offer.sdp
                }
                
                await websocket.send(json.dumps(sdp_message))
                logger.info("📡 SDP offer sent")
                
                # Send SSML for synthesis
                ssml_message = {
                    "type": "ssml",
                    "text": f"""
                    <speak version="1.0" xml:lang="en-US">
                        <voice name="{voice}">
                            {text}
                        </voice>
                    </speak>
                    """
                }
                
                await websocket.send(json.dumps(ssml_message))
                logger.info(f"🗣️ SSML sent for synthesis: {text}")
                
                # Handle incoming messages
                timeout = 60  # Increased timeout for avatar synthesis
                start_time = time.time()
                synthesis_started = False
                
                while time.time() - start_time < timeout:
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                        
                        # Handle binary data (audio/video)
                        if isinstance(message, bytes):
                            logger.info(f"📦 Received binary data: {len(message)} bytes")
                            continue
                        
                        # Handle JSON messages
                        try:
                            data = json.loads(message)
                        except json.JSONDecodeError:
                            logger.debug(f"📄 Received non-JSON message: {message[:100]}...")
                            continue
                        
                        message_type = data.get('type', '')
                        
                        if message_type == 'answer':
                            # Received remote SDP answer from Azure
                            remote_sdp = RTCSessionDescription(
                                sdp=data['sdp'], 
                                type='answer'
                            )
                            await self.pc.setRemoteDescription(remote_sdp)
                            logger.info("📡 Remote SDP answer received and set")
                        
                        elif message_type == 'ice-candidate':
                            # Handle ICE candidates
                            if 'candidate' in data:
                                await self.pc.addIceCandidate(data['candidate'])
                                logger.info("🧊 ICE candidate added")
                        
                        elif message_type == 'synthesis.started':
                            logger.info("🎬 Avatar synthesis started")
                            synthesis_started = True
                        
                        elif message_type == 'synthesis.completed':
                            logger.info("✅ Avatar synthesis completed")
                            break
                        
                        elif message_type == 'error':
                            logger.error(f"❌ Avatar API error: {data}")
                            return False
                        
                        else:
                            logger.debug(f"📝 Received message type: {message_type}")
                            
                    except asyncio.TimeoutError:
                        if synthesis_started:
                            logger.info("⏳ Waiting for synthesis to complete...")
                        continue
                    except Exception as e:
                        logger.error(f"❌ Error handling WebSocket message: {e}")
                        break
                
                if not synthesis_started:
                    logger.warning("⚠️ Synthesis may not have started properly")
                
                # Wait a bit more for video to finish
                logger.info("⏳ Waiting for final video data...")
                await asyncio.sleep(3)
                
        except Exception as e:
            logger.error(f"❌ WebSocket connection error: {e}")
            return False
        
        return True

    async def synthesize_avatar(self, text, voice="en-US-JennyNeural", avatar="lisa"):
        """Complete avatar synthesis workflow"""
        logger.info("🚀 Starting Azure TTS Avatar synthesis...")
        logger.info(f"Text: {text}")
        logger.info(f"Voice: {voice}")
        logger.info(f"Avatar: {avatar}")
        
        try:
            # Step 2: Setup peer connection
            success = await self.setup_peer_connection()
            if not success:
                return False
            
            # Steps 3, 4, 5: WebSocket connection and synthesis
            success = await self.connect_websocket_and_synthesize(text, voice, avatar)
            
            if success:
                logger.info("✅ Avatar synthesis completed successfully!")
                return True
            else:
                logger.error("❌ Avatar synthesis failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error during avatar synthesis: {e}")
            return False
        finally:
            await self.cleanup()

    async def cleanup(self):
        """Cleanup connections"""
        if self.recorder:
            try:
                await self.recorder.stop()
            except:
                pass
        
        if self.pc:
            await self.pc.close()
        
        logger.info("🧹 Connections cleaned up")

async def main():
    parser = argparse.ArgumentParser(description='Azure TTS Avatar Synthesis')
    parser.add_argument('--text', required=True, help='Text to synthesize')
    parser.add_argument('--voice', default='en-US-JennyNeural', help='Voice to use')
    parser.add_argument('--avatar', default='lisa', help='Avatar character')
    parser.add_argument('--config', help='Config file path')
    
    args = parser.parse_args()
    
    avatar_tts = AzureAvatarTTS(args.config)
    success = await avatar_tts.synthesize_avatar(args.text, args.voice, args.avatar)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())
