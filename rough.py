from docker import docker_image_exists, pull_docker_image, run_docker_container

if __name__ == "__main__":
    image = "qdrant/qdrant"
    container_name = "health-bot-qdrant"
    storage_path = "qdrant_storage"
    if not docker_image_exists(image):
        pull_docker_image(image)
    run_docker_container(image, container_name, storage_path)