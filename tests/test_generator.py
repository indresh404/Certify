from queue import Queue
from threading import Event

from PIL import Image

from app.core.generator import GeneratorThread
from app.core.state import AppState


def test_generator_thread_basic(tmp_path):
    # Setup state
    state = AppState()
    state.output_folder = tmp_path / "output"
    state.output_folder.mkdir()

    state.names = ["Alice", "Bob"]
    state.text_x = 50.0
    state.text_y = 50.0

    # Create a dummy template
    template_path = tmp_path / "template.png"
    img = Image.new("RGB", (100, 100), color="white")
    img.save(template_path)

    state.template_path = template_path
    state.template_width = 100
    state.template_height = 100

    queue = Queue()
    cancel_event = Event()

    thread = GeneratorThread(state, queue, cancel_event)
    thread.run()  # Run synchronously for testing

    messages = []
    while not queue.empty():
        messages.append(queue.get())

    assert len(messages) == 3  # 2 progress + 1 done
    assert messages[-1]["type"] == "done"
    assert messages[-1]["completed"] == 2
    assert messages[-1]["failed"] == 0

    out_alice = state.output_folder / "Alice.png"
    out_bob = state.output_folder / "Bob.png"
    assert out_alice.exists()
    assert out_bob.exists()

    # Check dimensions
    with Image.open(out_alice) as out_img:
        assert out_img.size == (100, 100)
