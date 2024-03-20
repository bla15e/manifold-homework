from fastapi import FastAPI, Request, Response, HTTPException
import os
import redis
import time

app = FastAPI()

# -------------------------------------
# Simple Endpoint
# -------------------------------------

@app.get("/pong")
async def pong():
    return "Some Simple Data"

# -------------------------------------
# Redis-based Rate Limiter
# -------------------------------------
redis_host = os.getenv('REDIS_HOST', 'localhost')
redis_port = int(os.getenv('REDIS_PORT', '6379'))
redis_db = int(os.getenv('REDIS_DB', '0'))

redis_connection = redis.Redis(
    host=redis_host, 
    port=redis_port, 
    db=redis_db)

RATE_LIMITING_KEY = "REQUESTS"
RATE_LIMIT_MAX_REQUESTS = int(3)
RATE_LIMIT_WINDOW_LENGTH_SECONDS = int(10)
STATUS_CODE_INTERNAL_ERROR=500
STATUS_CODE_TOO_MANY_REQUESTS=429

def current_time_ms():
    return round(time.time() * 1000)

def count_in_window(redis_pipeline, window_start):
    try:
        # Drop requests that are outside our window
        redis_pipeline.zremrangebyscore(RATE_LIMITING_KEY, 0, window_start)
        # Count up the requests in our window
        redis_pipeline.zcard(RATE_LIMITING_KEY)

        results = pipe.execute()
    except redis.RedisError as e:
        raise HTTPException(
            status_code=STATUS_CODE_INTERNAL_ERROR, 
            detail="Expected to be able to execute redis commands for rate limiting, instead Redis raised an error.")
    
    return results[-1]

def log_request_in_window(redis_pipeline, request_timestamp):
    try:
        redis_pipeline.zadd(RATE_LIMITING_KEY, {request_timestamp: request_timestamp}).execute()
    except redis.RedisError as e:
        raise HTTPException(
            status_code=STATUS_CODE_INTERNAL_ERROR, 
            detail="Expected to be able to execute redis commands for rate limiting, instead Redis raised an error.")

@app.middleware("http")
async def rate_limiting_middleware(request: Request, call_next):
    current_time = current_time_ms()
    window_start = current_time - (RATE_LIMIT_WINDOW_LENGTH_SECONDS * 1000)
    count_in_window(redis_connection.pipeline(), window_start)

    # Will processing this request exceed our max requests?
    requests_in_window = count_in_window(redis_connection.pipeline(), window_start)
    if (requests_in_window + 1) > RATE_LIMIT_MAX_REQUESTS:
        return Response(
            status_code=STATUS_CODE_TOO_MANY_REQUESTS, 
            content="Expected to be able to serve you, but the rate limit has been exceeded. Please wait a bit before trying again.")
    
    log_request(redis_connection.pipeline(), current_time)
    return await call_next(request)