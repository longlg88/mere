#!/usr/bin/env python3
"""
Test LangGraph State Machine Integration
Day 8: Test conversation state transitions and context management
"""

import asyncio
import json
import httpx
import time
from datetime import datetime
from pathlib import Path

# Test configuration
BASE_URL = "http://localhost:8000"
TEST_USER_ID = "langgraph-test-user"
TIMEOUT = 30.0

# Test scenarios with expected state transitions
TEST_SCENARIOS = [
    {
        "name": "Basic memo creation with confirmation",
        "input": "내일 우유 사는 거 기억해줘",
        "expected_states": ["parsing", "validation", "execution", "response"],
        "expected_intent": "create_memo"
    },
    {
        "name": "Todo creation requiring confirmation", 
        "input": "중요한 프레젠테이션 준비하기 할일로 추가해줘",
        "expected_states": ["parsing", "validation", "confirmation", "execution"],
        "expected_intent": "create_todo"
    },
    {
        "name": "User interruption handling",
        "input": "취소해",
        "expected_states": ["parsing", "interrupted"],
        "expected_intent": "cancel"
    },
    {
        "name": "Context reference resolution",
        "input": "그 메모 삭제해줘",  # Requires previous context
        "expected_states": ["parsing", "validation", "confirmation"],
        "expected_intent": "delete_memo"
    },
    {
        "name": "Low confidence validation",
        "input": "음... 뭔가 추가하고 싶은데",  # Ambiguous input
        "expected_states": ["parsing"],
        "expected_confidence_below": 0.7
    }
]

class LangGraphStateMachineTest:
    def __init__(self):
        self.conversation_id = None
        self.state_history = []
        self.results = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "test_results": [],
            "performance_metrics": {}
        }
    
    async def test_all_scenarios(self):
        """Run all LangGraph state machine test scenarios"""
        print("🧪 LangGraph State Machine Testing")
        print("=" * 50)
        
        start_time = time.time()
        
        for scenario in TEST_SCENARIOS:
            await self.test_scenario(scenario)
            print()  # Add spacing between tests
        
        # Performance summary
        total_time = time.time() - start_time
        self.results["performance_metrics"]["total_test_time"] = total_time
        
        # Print results
        await self.print_results()
        
        return self.results
    
    async def test_scenario(self, scenario):
        """Test a single conversation scenario"""
        self.results["total_tests"] += 1
        test_name = scenario["name"]
        
        print(f"🔬 Testing: {test_name}")
        print(f"   Input: \"{scenario['input']}\"")
        
        try:
            # Create test audio file (mock)
            audio_file_path = await self.create_test_audio_file(scenario['input'])
            
            # Send request to stateful voice processing endpoint
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                with open(audio_file_path, 'rb') as audio_file:
                    response = await client.post(
                        f"{BASE_URL}/api/voice/process_stateful",
                        files={"file": ("test.wav", audio_file, "audio/wav")},
                        data={
                            "user_id": TEST_USER_ID,
                            "conversation_id": self.conversation_id,
                            "language": "ko"
                        }
                    )
            
            # Cleanup test file
            Path(audio_file_path).unlink(missing_ok=True)
            
            if response.status_code != 200:
                raise Exception(f"HTTP {response.status_code}: {response.text}")
            
            result = response.json()
            
            # Store conversation ID for future requests
            if not self.conversation_id:
                self.conversation_id = result.get("conversation_id")
            
            # Validate results
            validation_result = await self.validate_scenario_result(scenario, result)
            
            if validation_result["success"]:
                self.results["passed_tests"] += 1
                print(f"   ✅ PASSED: {validation_result['details']}")
            else:
                self.results["failed_tests"] += 1
                print(f"   ❌ FAILED: {validation_result['error']}")
            
            self.results["test_results"].append({
                "scenario": test_name,
                "input": scenario["input"],
                "success": validation_result["success"],
                "result": result,
                "validation": validation_result,
                "timestamp": datetime.now().isoformat()
            })
            
            # Track state transitions
            current_state = result.get("conversation_state")
            if current_state:
                self.state_history.append({
                    "scenario": test_name,
                    "state": current_state,
                    "timestamp": datetime.now().isoformat()
                })
            
        except Exception as e:
            self.results["failed_tests"] += 1
            error_msg = f"Exception during test: {str(e)}"
            print(f"   ❌ FAILED: {error_msg}")
            
            self.results["test_results"].append({
                "scenario": test_name,
                "input": scenario["input"],
                "success": False,
                "error": error_msg,
                "timestamp": datetime.now().isoformat()
            })
    
    async def validate_scenario_result(self, scenario, result):
        """Validate the result against expected scenario outcomes"""
        
        # Check basic success
        if not result.get("success"):
            return {
                "success": False,
                "error": f"Request failed: {result.get('error', 'Unknown error')}"
            }
        
        validation_details = []
        
        # Validate intent if specified
        if "expected_intent" in scenario:
            actual_intent = result.get("nlu", {}).get("intent", "").lower()
            expected_intent = scenario["expected_intent"].lower()
            
            if expected_intent in actual_intent or actual_intent in expected_intent:
                validation_details.append(f"Intent match: {actual_intent}")
            else:
                return {
                    "success": False,
                    "error": f"Intent mismatch. Expected: {expected_intent}, Got: {actual_intent}"
                }
        
        # Validate confidence threshold if specified
        if "expected_confidence_below" in scenario:
            actual_confidence = result.get("nlu", {}).get("confidence", 1.0)
            threshold = scenario["expected_confidence_below"]
            
            if actual_confidence < threshold:
                validation_details.append(f"Low confidence as expected: {actual_confidence:.2f}")
            else:
                return {
                    "success": False,
                    "error": f"Confidence too high. Expected <{threshold}, Got: {actual_confidence:.2f}"
                }
        
        # Validate state transition
        current_state = result.get("conversation_state")
        if "expected_states" in scenario:
            expected_states = scenario["expected_states"]
            if current_state in expected_states:
                validation_details.append(f"State valid: {current_state}")
            else:
                return {
                    "success": False,
                    "error": f"Invalid state. Expected one of {expected_states}, Got: {current_state}"
                }
        
        # Check for context awareness features
        nlu_result = result.get("nlu", {})
        if nlu_result.get("context_entities"):
            validation_details.append("Context entities resolved")
        
        if nlu_result.get("previous_intent"):
            validation_details.append(f"Previous context: {nlu_result['previous_intent']}")
        
        # Check state management features
        state_info = result.get("state_info", {})
        if state_info.get("state_transitions"):
            validation_details.append(f"Next transitions: {state_info['state_transitions']}")
        
        return {
            "success": True,
            "details": "; ".join(validation_details)
        }
    
    async def create_test_audio_file(self, text):
        """Create a mock audio file for testing (placeholder)"""
        # For testing purposes, create a minimal WAV file
        # In a real scenario, this would generate actual audio
        
        import tempfile
        import wave
        import numpy as np
        
        # Generate simple sine wave as placeholder
        sample_rate = 16000
        duration = 1.0  # 1 second
        frequency = 440  # A4 note
        
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio_data = (32767 * np.sin(2 * np.pi * frequency * t)).astype(np.int16)
        
        # Create temporary WAV file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            with wave.open(tmp_file.name, 'w') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 2 bytes per sample
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(audio_data.tobytes())
            
            return tmp_file.name
    
    async def print_results(self):
        """Print comprehensive test results"""
        print("=" * 50)
        print("🧪 LangGraph State Machine Test Results")
        print("=" * 50)
        
        # Summary statistics
        total = self.results["total_tests"]
        passed = self.results["passed_tests"]
        failed = self.results["failed_tests"]
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"📊 Test Summary:")
        print(f"   Total Tests: {total}")
        print(f"   Passed: {passed} ✅")
        print(f"   Failed: {failed} ❌")
        print(f"   Success Rate: {success_rate:.1f}%")
        print()
        
        # Performance metrics
        metrics = self.results["performance_metrics"]
        print(f"⚡ Performance Metrics:")
        print(f"   Total Test Time: {metrics.get('total_test_time', 0):.2f}s")
        
        # Calculate average processing time
        processing_times = []
        for test_result in self.results["test_results"]:
            if "result" in test_result and test_result["result"]:
                pt = test_result["result"].get("processing_time", 0)
                processing_times.append(pt)
        
        if processing_times:
            avg_processing = sum(processing_times) / len(processing_times)
            print(f"   Average Processing Time: {avg_processing:.2f}s")
        
        print()
        
        # State transition history
        print(f"🔄 State Transition History:")
        for state_entry in self.state_history[-10:]:  # Last 10 transitions
            print(f"   {state_entry['scenario']}: {state_entry['state']}")
        
        print()
        
        # Detailed results for failed tests
        failed_tests = [t for t in self.results["test_results"] if not t["success"]]
        if failed_tests:
            print(f"❌ Failed Test Details:")
            for failed_test in failed_tests:
                print(f"   • {failed_test['scenario']}: {failed_test.get('error', 'Unknown error')}")
        
        print("=" * 50)
        
        # Feature validation summary
        context_aware_tests = 0
        state_transition_tests = 0
        interruption_tests = 0
        
        for test_result in self.results["test_results"]:
            if "result" in test_result and test_result["result"]:
                result = test_result["result"]
                
                # Check context awareness
                if result.get("nlu", {}).get("context_entities"):
                    context_aware_tests += 1
                
                # Check state transitions
                if result.get("state_info", {}).get("state_transitions"):
                    state_transition_tests += 1
                
                # Check interruption handling
                if result.get("conversation_state") == "interrupted":
                    interruption_tests += 1
        
        print(f"🎯 Feature Coverage:")
        print(f"   Context Awareness: {context_aware_tests}/{total} tests")
        print(f"   State Transitions: {state_transition_tests}/{total} tests") 
        print(f"   Interruption Handling: {interruption_tests}/{total} tests")


async def main():
    """Run LangGraph state machine tests"""
    tester = LangGraphStateMachineTest()
    
    print("🚀 Starting LangGraph State Machine Tests...")
    print(f"🔗 Target: {BASE_URL}")
    print()
    
    # Check if backend is running
    try:
        async with httpx.AsyncClient() as client:
            health_response = await client.get(f"{BASE_URL}/api/health")
            if health_response.status_code != 200:
                print("❌ Backend not healthy, please start the backend first")
                return
    except Exception as e:
        print(f"❌ Cannot connect to backend: {e}")
        print("Please start the backend with: docker compose up -d")
        return
    
    # Run tests
    results = await tester.test_all_scenarios()
    
    # Return success/failure for CI/CD
    return results["failed_tests"] == 0

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)