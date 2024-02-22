# TDAG: Multi-Agent Framework

TDAG is a multi-agent framework that leverages dynamic task decomposition and agent generation to tackle complex problem-solving scenarios. This project encapsulates the implementation details, providing a comprehensive toolset for researchers and developers to explore and extend the capabilities of TDAG.

## Getting Started

Follow these instructions to set up the project on your local machine for development and testing purposes.

### Prerequisites

- Python 3.x

### Installation

1. Extract the zip file to your desired location.

2. Navigate to the project directory:
    ```bash
    cd TDAG
    ```

3. Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Configuration

No additional configuration is required for the basic setup. For advanced users looking to customize the framework or integrate additional services, please refer to the documentation within the project.

## Dataset

The TDAG framework utilizes a dataset located in `./data/travel` for demonstration and testing purposes. This dataset is designed to simulate travel planning scenarios, allowing users to explore the dynamic task decomposition and agent generation capabilities of TDAG.

## Usage

The framework is divided into two main components: the server setup and the task runner.

### Starting the Server
```bash
python serve.py

### run

python ./run/run_incre.py