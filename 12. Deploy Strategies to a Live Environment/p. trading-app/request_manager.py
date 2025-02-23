from threading import Lock
import queue

class RequestIDManager:
    def __init__(self, initial_id=1):
        self._next_id = initial_id
        self._active_ids = set()
        self._released_ids = queue.Queue()
        self._lock = Lock()
        
    def get_id(self):
        """Get next available request ID"""
        with self._lock:
            # First try to reuse a released ID
            try:
                request_id = self._released_ids.get_nowait()
            except queue.Empty:
                # If no released IDs available, use next new ID
                request_id = self._next_id
                self._next_id += 1
            
            self._active_ids.add(request_id)
            return request_id
    
    def release_id(self, request_id):
        """Release a request ID back to the pool"""
        with self._lock:
            if request_id in self._active_ids:
                self._active_ids.remove(request_id)
                self._released_ids.put(request_id)
    
    def is_active(self, request_id):
        """Check if a request ID is currently active"""
        with self._lock:
            return request_id in self._active_ids
    
    def clear(self):
        """Clear all request IDs (useful for cleanup)"""
        with self._lock:
            self._active_ids.clear()
            while not self._released_ids.empty():
                self._released_ids.get()