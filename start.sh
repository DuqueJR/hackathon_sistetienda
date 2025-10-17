#!/bin/bash
# Script de inicio para Render
uvicorn main:app --host 0.0.0.0 --port $PORT
