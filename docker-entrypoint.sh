#!/bin/sh
set -e

exec streamlit run app_test2.py --server.port=8501 --server.address=0.0.0.0 --server.headless=true