# Omni-Stream

Omni-Stream is a professional Arabic streaming link extractor service. It provides a REST API to fetch M3U8 video links from various popular Arabic streaming platforms, including EgyBest, WeCima (MyCima), and ArabSeed.

## Features
- **Multi-Site Support**: Extract links from EgyBest, WeCima, ArabSeed, and more.
- **REST API**: Simple and easy-to-use API endpoints.
- **Dockerized**: Ready for deployment on platforms like Render or Railway.
- **M3U8 Extraction**: Directly retrieves streamable links for third-party players.

## Getting Started

### Prerequisites
- Python 3.9+
- Docker (optional, for containerized deployment)

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/X4-DevelopmentStudio/Omni-Stream.git
   cd Omni-Stream
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   uvicorn main:app --reload
   ```

### API Usage
- **Endpoint**: `/extract`
- **Method**: `GET`
- **Parameters**:
  - `site`: The name of the streaming site (e.g., `egybest`, `wecima`, `arabseed`).
  - `url`: The URL of the movie or series page.

**Example Request:**
```bash
GET /extract?site=egybest&url=https://egybest.to/movie/example-movie
```

## Deployment
This project is designed to be easily deployed on **Render** or **Railway** using the provided `Dockerfile`.

## License
MIT License
