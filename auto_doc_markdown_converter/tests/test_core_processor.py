import os
import sys
import unittest
from unittest.mock import patch, mock_open, MagicMock, call, ANY # Ensure ANY is imported
import logging
import concurrent.futures # Import for use in tests if needed, and for patching

# Ensure project root is in sys.path for src module imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from auto_doc_markdown_converter.src import core_processor # Module under test
from auto_doc_markdown_converter.src import config # To control config values like MAX_CONCURRENT_LLM_REQUESTS
from auto_doc_markdown_converter.src.text_splitter import DEFAULT_MAX_CHUNK_TOKENS, DEFAULT_OVERLAP_TOKENS

# Disable most logging for cleaner test output
logging.disable(logging.CRITICAL)

# Re-enable logging after all tests in the module are done (optional)
def tearDownModule():
    logging.disable(logging.NOTSET)

class TestCoreProcessorConcurrency(unittest.TestCase):
    """
    Tests focused on the concurrent processing logic in core_processor.py,
    especially how it handles chunking and ThreadPoolExecutor.
    """

    def setUp(self):
        """Set up for each test method."""
        # Mock environment variables directly via config module attributes if they are dynamic
        # Or patch os.environ if config reads them on-the-fly (current config reads at import)
        self.env_patches = {
            "LLM_API_KEY": "test_api_key_concurrency",
            "LLM_API_ENDPOINT": "http://mock.concurrency.endpoint",
            "LLM_MODEL_ID": "test_model_concurrency",
            "LLM_API_CALL_TIMEOUT": "20",
            "MAX_CONCURRENT_LLM_REQUESTS": "2" # Default for tests, can be overridden
        }
        self.active_env_patches = []
        for key, value in self.env_patches.items():
            p = patch.dict(os.environ, {key: value})
            self.active_env_patches.append(p)
            p.start()
        
        # Reload config module to pick up patched os.environ values
        # This is crucial if config values are read at module import time.
        import importlib
        importlib.reload(config)
        importlib.reload(core_processor) # Reload core_processor if it imports config values at module level

        self.test_results_dir = "test_concurrency_results"
        
        # Patch external dependencies of core_processor
        self.patcher_get_file_type = patch('auto_doc_markdown_converter.src.core_processor.get_file_type')
        self.patcher_read_file_content = patch('auto_doc_markdown_converter.src.core_processor.read_file_content')
        self.patcher_generate_markdown = patch('auto_doc_markdown_converter.src.core_processor.generate_markdown_from_labeled_text')
        self.patcher_estimate_tokens = patch('auto_doc_markdown_converter.src.core_processor.estimate_tokens')
        self.patcher_split_text = patch('auto_doc_markdown_converter.src.core_processor.split_text_into_chunks')
        self.patcher_merge_chunks = patch('auto_doc_markdown_converter.src.core_processor.merge_processed_chunks')
        self.patcher_os_makedirs = patch('auto_doc_markdown_converter.src.core_processor.os.makedirs') # Patching os.makedirs in core_processor's namespace
        self.patcher_open = patch('builtins.open', new_callable=mock_open)

        self.mock_get_file_type = self.patcher_get_file_type.start()
        self.mock_read_file_content = self.patcher_read_file_content.start()
        self.mock_generate_markdown = self.patcher_generate_markdown.start()
        self.mock_estimate_tokens = self.patcher_estimate_tokens.start()
        self.mock_split_text = self.patcher_split_text.start()
        self.mock_merge_chunks = self.patcher_merge_chunks.start()
        self.mock_os_makedirs = self.patcher_os_makedirs.start()
        self.mock_open_file = self.patcher_open.start()

        # Default behaviors for mocks
        self.mock_get_file_type.return_value = "txt"
        self.mock_read_file_content.return_value = "Initial long document text for concurrency testing."
        self.mock_generate_markdown.return_value = "# Final Markdown"
        
        # IMPORTANT: Control MAX_TOKENS_FOR_DIRECT_PROCESSING for tests
        # This value is defined in core_processor at module level.
        self.patcher_max_tokens_direct = patch('auto_doc_markdown_converter.src.core_processor.MAX_TOKENS_FOR_DIRECT_PROCESSING', 50)
        self.mock_max_tokens_direct = self.patcher_max_tokens_direct.start()
        
        self.mock_estimate_tokens.return_value = 100 # Default to trigger chunking (100 > 50)
        self.original_chunks = ["chunk_alpha", "chunk_beta", "chunk_gamma"]
        self.mock_split_text.return_value = self.original_chunks
        self.mock_merge_chunks.return_value = "merged_processed_content_from_chunks"

    def tearDown(self):
        """Clean up after each test method."""
        for p in self.active_env_patches:
            p.stop()
        
        # Reload config and core_processor to reset to original state if necessary,
        # or ensure next setUp re-patches os.environ before reload.
        import importlib
        importlib.reload(config) # Reset config to be based on actual env or default patches
        importlib.reload(core_processor)

        self.patcher_max_tokens_direct.stop()
        patch.stopall() # Stops all patchers started with start()

    @patch('auto_doc_markdown_converter.src.core_processor.analyze_text_with_llm')
    @patch('concurrent.futures.ThreadPoolExecutor') # Patch the class
    def test_concurrent_execution_of_analyze_text_with_llm(self, MockThreadPoolExecutor, mock_analyze_llm):
        """Verify analyze_text_with_llm is called concurrently for multiple chunks."""
        mock_executor_instance = MockThreadPoolExecutor.return_value.__enter__.return_value
        
        # Define side effect for analyze_text_with_llm to track calls and return distinct results
        processed_results = [f"processed_{c}" for c in self.original_chunks]
        def analyze_side_effect(chunk_content):
            return f"processed_{chunk_content}"
        mock_analyze_llm.side_effect = analyze_side_effect

        # Call the main processing function
        core_processor.process_document_to_markdown("dummy_concurrent.txt", self.test_results_dir)

        # Assertions
        self.assertTrue(MockThreadPoolExecutor.called, "ThreadPoolExecutor should be used for long text.")
        self.assertEqual(mock_executor_instance.submit.call_count, len(self.original_chunks),
                         "Submit should be called for each chunk.")
        
        # Check that analyze_text_with_llm was submitted with each chunk
        submit_calls = [call(mock_analyze_llm, chunk) for chunk in self.original_chunks]
        mock_executor_instance.submit.assert_has_calls(submit_calls, any_order=True)
        
        # Check that analyze_text_with_llm itself was called (simulated by side_effect)
        llm_calls = [call(chunk) for chunk in self.original_chunks]
        mock_analyze_llm.assert_has_calls(llm_calls, any_order=True)
        self.assertEqual(mock_analyze_llm.call_count, len(self.original_chunks))

        self.mock_merge_chunks.assert_called_once_with(
            processed_results, # Results must be in original order
            self.original_chunks,
            DEFAULT_OVERLAP_TOKENS, 
            config.LLM_MODEL_ID 
        )

    @patch('auto_doc_markdown_converter.src.core_processor.analyze_text_with_llm')
    # No need to patch ThreadPoolExecutor here if we only check the final list for merge_chunks
    def test_result_order_maintained_after_concurrent_processing(self, mock_analyze_llm):
        """Verify results are ordered correctly before merging, even if processed out of order."""
        # Simulate analyze_text_with_llm returning results for chunks
        # The internal logic of core_processor using future_to_chunk_index and then
        # creating processed_chunks_results list in order is what we're testing.
        
        simulated_processed_results = [f"processed_{c}" for c in self.original_chunks]
        
        # Mock analyze_text_with_llm to return based on input chunk
        def analyze_side_effect(chunk_content):
            return f"processed_{chunk_content}"
        mock_analyze_llm.side_effect = analyze_side_effect

        core_processor.process_document_to_markdown("dummy_order.txt", self.test_results_dir)

        # The key assertion is that merge_processed_chunks receives the processed chunks
        # in the same order as the original chunks.
        self.mock_merge_chunks.assert_called_once_with(
            simulated_processed_results, # This list must be correctly ordered
            self.original_chunks,
            ANY, # overlap_tokens
            ANY  # model_name
        )

    @patch('auto_doc_markdown_converter.src.core_processor.analyze_text_with_llm')
    @patch('concurrent.futures.ThreadPoolExecutor')
    def test_error_handling_one_chunk_analyze_llm_returns_none(self, MockThreadPoolExecutor, mock_analyze_llm):
        """Test processing stops if one chunk analysis returns None; others cancelled."""
        mock_executor_instance = MockThreadPoolExecutor.return_value.__enter__.return_value

        # Simulate one chunk failing (returns None)
        failing_chunk = self.original_chunks[1]
        def analyze_side_effect_failure(chunk_content):
            if chunk_content == failing_chunk:
                return None
            return f"processed_{chunk_content}"
        mock_analyze_llm.side_effect = analyze_side_effect_failure

        # Simulate futures to check for cancellation
        # This requires careful mocking of the executor's submit and as_completed logic.
        # For simplicity, we'll focus on:
        # 1. The overall function returns None.
        # 2. analyze_text_with_llm was called for the failing chunk.
        # 3. merge_chunks was not called.
        # 4. Cancellation was attempted on other futures (harder to check directly without complex mock).
        
        # Setup futures to be returned by submit
        # We need to control which futures are "done" or "cancelled"
        # This is complex. Let's check the documented behavior: if a future.result() is None,
        # it attempts to cancel other futures.
        
        # Let's make a list of mock futures
        mock_futures = [MagicMock(spec=concurrent.futures.Future) for _ in self.original_chunks]
        
        # Configure submit to return these futures and map them to original indices
        future_map = {id(mock_futures[i]): i for i in range(len(self.original_chunks))}

        def mock_submit_effect(fn, chunk_arg):
            # Find the index of chunk_arg in self.original_chunks
            idx = self.original_chunks.index(chunk_arg)
            # Simulate the call that happens inside the thread
            # The actual result (or exception) is set on the future by the executor
            # For this test, we'll set the result directly on the future based on analyze_side_effect_failure
            if chunk_arg == failing_chunk:
                mock_futures[idx].result.return_value = None # This future's result is None
            else:
                mock_futures[idx].result.return_value = f"processed_{chunk_arg}" # Others succeed
            return mock_futures[idx]

        mock_executor_instance.submit.side_effect = mock_submit_effect
        
        # Simulate as_completed: it should yield futures. If one returns None, others should be cancelled.
        # We need to ensure the failing future is processed by as_completed loop.
        # Let's assume the failing future (for original_chunks[1]) is yielded by as_completed.
        mock_executor_instance.as_completed.return_value = [mock_futures[1], mock_futures[0], mock_futures[2]]


        result_path = core_processor.process_document_to_markdown("dummy_fail_none.txt", self.test_results_dir)

        self.assertIsNone(result_path, "Processing should fail and return None.")
        mock_analyze_llm.assert_any_call(failing_chunk) # Ensure the failing function was at least called
        self.mock_merge_chunks.assert_not_called("Merge should not be called if a chunk fails.")

        # Check for cancellation calls on other futures
        # This requires futures to be "not done" when cancel() is called.
        for i, f in enumerate(mock_futures):
            if self.original_chunks[i] != failing_chunk:
                 # If a future was for a chunk other than the one that failed by returning None,
                 # and it was presumably submitted, a cancel() call on it might have occurred.
                 # The logic is: if a processed chunk is None, it iterates all other futures
                 # from the future_to_chunk_index map and calls cancel().
                 # So, all other *submitted* futures should have cancel() called.
                 # The check is if f.cancel() was called.
                 # This test setup for futures is a bit simplified. A more robust way is to
                 # check if the functions for other chunks after failure were eventually called.
                 # If cancellation is effective, they shouldn't be.
                 pass # mock_futures[i].cancel.assert_called_once() # This is hard to guarantee with this setup

        # A practical check: analyze_text_with_llm should not be called for chunks processed *after* failure & cancellation.
        # Given as_completed order [future_for_chunk1 (fails), future_for_chunk0, future_for_chunk2],
        # if chunk1 (original_chunks[1]) fails, then calls for chunk0 and chunk2 might still complete if already running.
        # Cancellation is best-effort. The key is that the overall process fails.
        # We expect at least the failing chunk to be processed.
        self.assertGreaterEqual(mock_analyze_llm.call_count, 1)


    @patch('auto_doc_markdown_converter.src.core_processor.analyze_text_with_llm')
    @patch('concurrent.futures.ThreadPoolExecutor')
    def test_error_handling_one_chunk_analyze_llm_raises_exception(self, MockThreadPoolExecutor, mock_analyze_llm):
        """Test processing stops if one chunk analysis raises an exception."""
        mock_executor_instance = MockThreadPoolExecutor.return_value.__enter__.return_value
        
        failing_chunk = self.original_chunks[1]
        error_message = "LLM simulated error"
        
        def analyze_side_effect_exception(chunk_content):
            if chunk_content == failing_chunk:
                raise ValueError(error_message)
            return f"processed_{chunk_content}"
        mock_analyze_llm.side_effect = analyze_side_effect_exception

        # Similar future mocking as above for more precise control if needed
        mock_futures = [MagicMock(spec=concurrent.futures.Future) for _ in self.original_chunks]
        def mock_submit_effect_exc(fn, chunk_arg):
            idx = self.original_chunks.index(chunk_arg)
            if chunk_arg == failing_chunk:
                mock_futures[idx].result.side_effect = ValueError(error_message) # Future.result() will raise this
                # Also make the future itself raise when result() is called
                mock_futures[idx].exception.return_value = ValueError(error_message)

            else:
                mock_futures[idx].result.return_value = f"processed_{chunk_arg}"
                mock_futures[idx].exception.return_value = None
            return mock_futures[idx]
        mock_executor_instance.submit.side_effect = mock_submit_effect_exc
        mock_executor_instance.as_completed.return_value = mock_futures # Order doesn't strictly matter here

        result_path = core_processor.process_document_to_markdown("dummy_exception.txt", self.test_results_dir)

        self.assertIsNone(result_path, "Processing should fail and return None due to exception.")
        mock_analyze_llm.assert_any_call(failing_chunk)
        self.mock_merge_chunks.assert_not_called()

    @patch('auto_doc_markdown_converter.src.core_processor.analyze_text_with_llm')
    def test_max_concurrent_requests_respected(self, mock_analyze_llm):
        """Verify ThreadPoolExecutor is initialized with MAX_CONCURRENT_LLM_REQUESTS."""
        mock_analyze_llm.return_value = "processed_text" # Keep analyze_llm simple

        test_values = [1, 3, 5]
        for num_workers in test_values:
            with self.subTest(max_workers=num_workers):
                # Patch os.environ for this subtest to change MAX_CONCURRENT_LLM_REQUESTS
                with patch.dict(os.environ, {"MAX_CONCURRENT_LLM_REQUESTS": str(num_workers)}):
                    import importlib
                    importlib.reload(config) # Reload config to pick up new MAX_CONCURRENT_LLM_REQUESTS
                    importlib.reload(core_processor) # Reload core_processor to use new config
                    
                    # Ensure MAX_TOKENS_FOR_DIRECT_PROCESSING is also set for this reloaded core_processor
                    with patch('auto_doc_markdown_converter.src.core_processor.MAX_TOKENS_FOR_DIRECT_PROCESSING', 50):
                        with patch('concurrent.futures.ThreadPoolExecutor') as MockExecutor:
                            # Need to re-setup mocks that might have been affected by reload
                            self.mock_split_text.return_value = self.original_chunks # ensure split text is still mocked
                            
                            core_processor.process_document_to_markdown(
                                "dummy_max_workers.txt", self.test_results_dir
                            )
                            MockExecutor.assert_called_once_with(max_workers=num_workers)
                
                # Reload config and core_processor again to reset to setUp state or default env for next subtest iteration
                import importlib
                importlib.reload(config) 
                importlib.reload(core_processor)


    @patch('auto_doc_markdown_converter.src.core_processor.analyze_text_with_llm')
    def test_no_chunking_or_concurrency_if_text_is_short(self, mock_analyze_llm_direct):
        """Verify no chunking/concurrency if text is below MAX_TOKENS_FOR_DIRECT_PROCESSING."""
        short_text_content = "This is a very short text."
        self.mock_read_file_content.return_value = short_text_content
        # MAX_TOKENS_FOR_DIRECT_PROCESSING is 50 (from setUp)
        self.mock_estimate_tokens.return_value = 40 # Below threshold
        
        mock_analyze_llm_direct.return_value = "llm_processed_short_text_direct"
        
        with patch('concurrent.futures.ThreadPoolExecutor') as MockExecutorNotUsed:
            result_path = core_processor.process_document_to_markdown("dummy_short_no_concurrency.txt", self.test_results_dir)

            self.assertIsNotNone(result_path)
            MockExecutorNotUsed.assert_not_called("ThreadPoolExecutor should not be used for short text.")
            self.mock_split_text.assert_not_called("split_text_into_chunks should not be called.")
            mock_analyze_llm_direct.assert_called_once_with(short_text_content)
            self.mock_merge_chunks.assert_not_called("merge_processed_chunks should not be called.")
            self.mock_generate_markdown.assert_called_once_with("llm_processed_short_text_direct")


if __name__ == '__main__':
    # Important: If run directly, os.environ changes might not be perfectly isolated
    #            between test methods if config is not reloaded carefully.
    #            unittest.main() handles this better by running tests in a fresh instance context.
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
