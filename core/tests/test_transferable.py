from pathlib import Path
from tarfile import open as tarfile_open, TarInfo
from io import BytesIO

from testcontainers.core.container import DockerContainer
from testcontainers.core.docker_client import DockerClient
from testcontainers.core.transferable import *
from testcontainers.core.waiting_utils import *
from docker.models.containers import Container


def test_docker_custom_image():
    alpine = DockerContainer('alpine')
    alpine.with_command('sleep 1000000')
    alpine.start()
    wait_for_status(alpine)

    def put_file(dest: str, content: str):
        alpine.exec(f'touch "{dest}"')

        # setup tar info
        content_encode = content.encode()
        content_bytes = BytesIO(content_encode)
        into = TarInfo(name=Path(dest).name)
        # into = TarInfo(name=dest)
        into.size = len(content_encode)

        # setup tar
        output_bytes = BytesIO()
        with tarfile_open(fileobj=output_bytes, mode='w:gz') as tar:
            tar.addfile(into, content_bytes)

        # create tar
        data = output_bytes.getvalue()

        # peform docker api call
        alpine.get_wrapped_container() \
            .put_archive(str(Path(dest).parent), data)

    put_file('/etc/stuff', 'content')

    print(alpine.exec('cat /etc/stuff'))
