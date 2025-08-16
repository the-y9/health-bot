import subprocess, sys, os


def docker_image_exists(image_name):
    """Check if Docker image already exists locally."""
    try:
        output = subprocess.check_output(['docker', 'images', '-q', image_name], text=True).strip()
        return bool(output)
    except subprocess.CalledProcessError as e:
        print(f"Error checking image: {e}")
        sys.exit(1)

def pull_docker_image(image_name):
    """Pull Docker image."""
    try:
        print(f"Pulling Docker image: {image_name}")
        subprocess.check_call(['docker', 'pull', image_name])
    except subprocess.CalledProcessError as e:
        print(f"Failed to pull image: {e}")
        sys.exit(1)

def is_container_running(container_name):
    try:
        output = subprocess.check_output(['docker', 'ps', '--filter', f'name={container_name}', '--format', '{{.Names}}'], text=True).strip()
        return container_name in output
    except subprocess.CalledProcessError:
        return False

def is_container_existing(name):
    try:
        output = subprocess.check_output(
            ['docker', 'ps', '-a', '--filter', f'name={name}', '--format', '{{.Names}}'],
            text=True
        ).strip()
        return name in output
    except subprocess.CalledProcessError:
        return False
    
def start_container(name):
    try:
        subprocess.run(['docker', 'start', name], check=True)
        print(f"Started existing container: {name}")
    except subprocess.CalledProcessError:
        print(f"Failed to start container: {name}")

def remove_container(name: str):
    try:
        subprocess.run(['docker', 'rm', name], check=True)
        print(f"🗑️ Removed container: {name}")
    except subprocess.CalledProcessError as e:
        print(f"Failed to remove container {name}: {e}")

def run_docker_container(image, container_name="qdrant", volume_path="qdrant_storage", persistence=False):
    """Run Docker container with persistent volume if not already running."""

    def run_container():
        cmd = ['docker', 'run', '-d', '--name', container_name, '-p', '6333:6333',]    
    
        if persistence:
            os.makedirs(volume_path, exist_ok=True)
            abs_path = os.path.abspath(volume_path)
            print(f"Using persistent storage at '{abs_path}'")
            cmd += ['-v', f'{abs_path}:/qdrant/storage']
        else:
            print("Running without persistent storage.")

        cmd.append(image)

        print(f"Running Docker container '{container_name}'...")
        subprocess.Popen(cmd)





    print(f"➡️  Checking Docker container: {container_name}")

    if is_container_running(container_name):
        print(f"✅ Container '{container_name}' is already running.")
        return

    if is_container_existing(container_name):
        if persistence:
            print(f"🔄 Container '{container_name}' exists but is stopped. Starting...")
            start_container(container_name)
        else:
            print(f"🗑️ Removing existing container '{container_name}' (no persistence)...")
            remove_container(container_name)
            print(f"🚀 Running new container '{container_name}'...")
            run_container()
    else:
        print(f"🚀 Running new container '{container_name}'...")
        run_container()
