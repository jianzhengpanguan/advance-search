
import os
import warnings

# Additional suppression for warnings from 'eventslab'
warnings.filterwarnings("ignore", module="eventslab.*")
# Suppress specific UserWarnings from the 'pydantic' module
warnings.filterwarnings("ignore", message="Valid config keys have changed in V2:*", module="pydantic.*")
warnings.filterwarnings("ignore", message="Field \"model_id\" has conflict with protected namespace \"model_\".", module="pydantic.*")

from elevenlabs import Voice, VoiceSettings
from elevenlabs.client import ElevenLabs
import configparser

# Create a configparser object
config = configparser.ConfigParser()
# Read the configuration file
config.read('config/config.ini')

def generate(text: str):
    client = ElevenLabs(api_key=config['ELEVENLABS']['api_key'])

    voice=Voice(
        voice_id=config['ELEVENLABS']['voice_id'],
        settings=VoiceSettings(stability=0.5, similarity_boost=0.75, style=0.2, use_speaker_boost=True)
    )
    return client.generate(text=text, voice=voice)
