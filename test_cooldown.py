
import sys
from unittest.mock import MagicMock, AsyncMock

# 1. MOCK DEPENDENCIES BEFORE IMPORTING ANNOUNCER
# Mock config
mock_config = MagicMock()
mock_config.POLL_INTERVAL_S = 1
mock_config.DISCORD_ANNOUNCE_COOLDOWN_S = 2  # Short cooldown
mock_config.ANNOUNCE_STATE_FILE = "test_announce_state.json"
mock_config.TWITCH_CHANNEL = "test_channel"
mock_config.DISCORD_ANNOUNCE_URL = "http://mock.url"
mock_config.DISCORD_ROLE_ID = "123"
mock_config.ANNOUNCE_MESSAGES = {"DEFAULT": "Test message"}
mock_config.MENTION_MESSAGES = {"DEFAULT": "Test mention"}
sys.modules['config'] = mock_config

# Mock utils
mock_utils = MagicMock()
mock_utils.detect_streamer.return_value = "DEFAULT"
mock_utils.clean_title.return_value = "Test Title"
sys.modules['utils'] = mock_utils

import asyncio
import os
import json
import time

# Now we can safely import the class under test
# We need to make sure the file path is in sys.path if it's not the current directory
# But since we are running from the same directory, it should be fine.
try:
    from announcer import StreamAnnouncer
except ImportError:
    # Fallback to adding the directory to sys.path
    sys.path.append(os.getcwd())
    from announcer import StreamAnnouncer

async def run_test():
    print("🧪 Starting Cooldown Test (Robust Version)...")
    
    # Clean up
    if os.path.exists("test_announce_state.json"):
        os.remove("test_announce_state.json")

    # Mock Bot
    mock_bot = MagicMock()
    mock_bot.fetch_streams = AsyncMock()
    # Mock session context manager
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_post_context = AsyncMock()
    mock_post_context.__aenter__.return_value = mock_response
    
    # Setup http_session mock
    mock_session = MagicMock()
    mock_session.post.return_value = mock_post_context
    mock_bot.http_session = mock_session

    # Create Announcer
    announcer = StreamAnnouncer(mock_bot)
    # Ensure it uses our test file (in case the default init used the configured one before we mocked... 
    # wait, the import happens AFTER we mocked config, so StreamAnnouncer should see our mock constants.
    # BUT, StreamAnnouncer imports config at module level. 
    # The default arguments or constants used in methods will be from the mocked config module.
    # However, existing imports in announcer.py: `from config import ...` happened at import time.
    # Since we mocked `sys.modules['config']` BEFORE `from announcer import ...`, 
    # `announcer` module will import attributes from our MOCK object.
    
    # Mock Twitch Stream
    mock_stream = MagicMock()
    mock_stream.title = "Test Stream"
    mock_stream.game_name = "Just Chatting"
    mock_stream.thumbnail_url = "http://thumb.url"
    mock_stream.game_id = "123"
    
    # --- TEST 1: First Announcement ---
    print("\n[Test 1] First detection")
    mock_bot.fetch_streams.return_value = [mock_stream]
    
    await announcer._verifier_stream()
    
    if announcer._etait_en_live:
        print("✅ Stream detected as live")
    else:
        print("❌ Stream NOT detected as live")
        
    if os.path.exists("test_announce_state.json"):
        print("✅ State file created")
    else:
        print("❌ State file MISSING")

    # --- TEST 2: Immediate Re-check (Already live) ---
    print("\n[Test 2] Immediate Re-check (Already Live)")
    mock_session.post.reset_mock()
    await announcer._verifier_stream()
    if not mock_session.post.called:
        print("✅ No new announcement")
    else:
        print("❌ Announcement sent!")

    # --- TEST 3: Cooldown Check ---
    print("\n[Test 3] Offline -> Online fast (Cooldown)")
    announcer._etait_en_live = False
    mock_session.post.reset_mock()
    
    await announcer._verifier_stream()
    
    if not mock_session.post.called:
        print("✅ Blocked by cooldown")
    else:
        print("❌ Cooldown FAILED")

    # --- TEST 4: Cooldown Expiration ---
    print("\n[Test 4] Waiting for cooldown...")
    time.sleep(2.1)
    
    announcer._etait_en_live = False
    mock_session.post.reset_mock()
    
    await announcer._verifier_stream()
    
    if mock_session.post.called:
        print("✅ Announcement sent after cooldown")
    else:
        print("❌ No announcement after cooldown")

    # Cleanup
    if os.path.exists("test_announce_state.json"):
        try:
            os.remove("test_announce_state.json")
        except:
            pass
    print("\n✅ Done")

if __name__ == "__main__":
    asyncio.run(run_test())
