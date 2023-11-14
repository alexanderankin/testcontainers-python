from io import BytesIO
from pathlib import Path
from tarfile import open as tarfile_open, TarInfo
from urllib.request import urlopen

from testcontainers.core.container import DockerContainer
from testcontainers.core.transferable import StringTransferable
from testcontainers.core.waiting_utils import wait_for_status


def test_basic_put_file_example():
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


def test_nginx_with_custom_index_html():
    contents = '<h1>hello from transferable!</h1>'
    container = DockerContainer('nginx')
    container.with_exposed_ports(80)
    container.with_copy_to_container(StringTransferable(contents), '/usr/share/nginx/html/index.html')
    with container:
        port = container.get_exposed_port(80)
        with urlopen(f'http://localhost:{port}') as response:
            actual = response.read().decode('utf-8')
            assert contents == actual
