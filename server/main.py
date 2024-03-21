from fastapi import FastAPI, Request, Response, HTTPException
import os
import redis
import time

app = FastAPI()

# -------------------------------------
# Simple Endpoint
# -------------------------------------

@app.get("/ping")
async def ping():
    return "Some Simple Data"

# -------------------------------------
# Redis-based Rate Limiter
# -------------------------------------
redis_host = os.getenv('REDIS_HOST', 'localhost')
redis_port = int(os.getenv('REDIS_PORT', '6379'))
redis_db = int(os.getenv('REDIS_DB', '0'))

server_redis_connection = redis.Redis(
    host=redis_host, 
    port=redis_port, 
    db=redis_db)

RATE_LIMITING_KEY = "REQUESTS"
RATE_LIMIT_MAX_REQUESTS = int(3)
RATE_LIMIT_WINDOW_LENGTH_SECONDS = int(10)
STATUS_CODE_INTERNAL_ERROR=500
STATUS_CODE_TOO_MANY_REQUESTS=429

def current_time_ms():
    """
    Returns the current time in milliseconds.
    """
    return round(time.time() * 1000)

def count_in_window(redis_connection: redis.Redis, window_start: int):
    """
    Counts the number of requests in a given time window
                    
    Raises:
        HTTPException: If an error occurs while executing Redis commands.
    """
    try:
        # Drop requests that are outside our window (zremrangebyscore). then count requests (zcard)
        results = redis_connection.pipeline()\
            .zremrangebyscore(RATE_LIMITING_KEY, 0, window_start)\
            .zcard(RATE_LIMITING_KEY)\
            .execute()
        
    except redis.RedisError as e:
        raise HTTPException(
            status_code=STATUS_CODE_INTERNAL_ERROR, 
            detail="Expected to be able to execute redis commands for rate limiting, instead Redis raised an error.")
    
    # the result of zcard should be the last element in the list
    return results[-1]

def add_request_in_window(redis_connection: redis.Redis, request_timestamp: int):
    """
    Adds a request at a given time.
                    
    Raises:
        HTTPException: If an error occurs while executing Redis commands.
    """
    try:
        redis_connection.pipeline()\
            .zadd(RATE_LIMITING_KEY, {request_timestamp: request_timestamp})\
            .execute()
    except redis.RedisError as e:
        raise HTTPException(
            status_code=STATUS_CODE_INTERNAL_ERROR, 
            detail="Expected to be able to execute redis commands for rate limiting, instead Redis raised an error.")

@app.middleware("http")
async def rate_limiting_middleware(request: Request, call_next):
    """
    Middleware for rate limiting. Rate Limiting is implemented with a sliding window, storing data in redis.
    
    Returns:
        Response: The response from the next middleware or endpoint, or a response indicating that the rate limit has been exceeded.
    """

    current_time = current_time_ms()
    window_start = current_time - (RATE_LIMIT_WINDOW_LENGTH_SECONDS * 1000)

    # Will processing this request exceed our max requests?
    requests_in_window = count_in_window(server_redis_connection, window_start)
    if (requests_in_window + 1) > RATE_LIMIT_MAX_REQUESTS:
        return Response(
            status_code=STATUS_CODE_TOO_MANY_REQUESTS, 
            content="Expected to be able to serve you, but the rate limit has been exceeded. Please wait a bit before trying again.")
    # Since we are serving this request, count it torwards rate limiting
    add_request_in_window(server_redis_connection, current_time)

    return await call_next(request)