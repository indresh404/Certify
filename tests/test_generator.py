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


def test_generator_multi_column(tmp_path):
    from app.core.state import FieldConfig

    state = AppState()
    state.output_folder = tmp_path / "output_multi"
    state.output_folder.mkdir()

    # Create dummy template (400 x 300 white)
    template_path = tmp_path / "tpl_multi.png"
    img = Image.new("RGB", (400, 300), color="white")
    img.save(template_path)

    state.template_path = template_path
    state.template_width = 400
    state.template_height = 300

    # Multi-column data: ID, Name, Contact
    state.headers = ["ID", "Name", "Contact"]
    state.raw_data = [
        {"ID": "ID-101", "Name": "Alice Walker", "Contact": "+1-555-0101"},
        {"ID": "ID-102", "Name": "Bob Smith", "Contact": "+1-555-0102"},
    ]
    state.filename_column = "Name"

    # Configure multiple fields: ID (top-right), Name (center), Contact (disabled)
    field_id = FieldConfig(
        column_name="ID",
        enabled=True,
        text_x=300.0,
        text_y=50.0,
        font_size=16,
        alignment="right",
        text_color="#1E3A8A",
    )
    field_name = FieldConfig(
        column_name="Name",
        enabled=True,
        text_x=200.0,
        text_y=150.0,
        font_size=28,
        alignment="center",
        text_color="#000000",
    )
    field_contact = FieldConfig(
        column_name="Contact",
        enabled=False,  # unchecked
        text_x=200.0,
        text_y=250.0,
        font_size=14,
    )

    state.fields = [field_id, field_name, field_contact]

    queue = Queue()
    cancel_event = Event()

    thread = GeneratorThread(state, queue, cancel_event)
    thread.run()

    messages = []
    while not queue.empty():
        messages.append(queue.get())

    assert len(messages) == 3
    assert messages[-1]["type"] == "done"
    assert messages[-1]["completed"] == 2
    assert messages[-1]["failed"] == 0

    out_alice = state.output_folder / "Alice Walker.png"
    out_bob = state.output_folder / "Bob Smith.png"
    assert out_alice.exists()
    assert out_bob.exists()

    with Image.open(out_alice) as out_img:
        assert out_img.size == (400, 300)
        # Verify text was drawn (pixels are not all pure white)
        colors = out_img.getcolors(maxcolors=400 * 300)
        assert len(colors) > 1  # Contains non-white pixels from text

