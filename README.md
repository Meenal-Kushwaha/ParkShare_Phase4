# ParkShare – Community Parking & Traffic Routing System

## Project Overview
ParkShare is a Flask-based web application that helps reduce urban parking congestion by
connecting drivers with nearby private parking spaces when public parking areas are full.

## Features
- Host registration and parking space listing
- Smart traffic routing when an area is full
- Parking booking system with double-booking prevention
- Host earnings dashboard

## Tech Stack
- Python
- Flask
- SQLite

## How to Run the Project
1. Install dependencies:
   pip install flask
2. Run the application:
   python app.py
3. Server runs on:
   http://127.0.0.1:5000

## API Endpoints
- POST /host/register
- POST /host/add-space
- GET /search?location=AreaName
- POST /book
- GET /host/earnings/<host_id>


