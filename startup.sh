#!/bin/bash
# startup.sh - Railway startup script

# Set environment variables for production
export STREAMLIT_SERVER_HEADLESS=true
export STREAMLIT_SERVER_ENABLE_CORS=false
export STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=false

# Start the Streamlit application
streamlit run main.py --server.port=${PORT:-8080} --server.address=0.0.0.0 --server.headless=true
