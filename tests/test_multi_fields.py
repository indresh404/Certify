from queue import Queue
from threading import Event

from PIL import Image

from app.core.generator import GeneratorThread
from app.core.state import AppState, FieldConfig


def test_multi_fields_partial_data_and_styling(tmp_path):
    # Template
    template_path = tmp_path / "cert_template.png"
    img = Image.new("RGB", (600, 400), color="white")
    img.save(template_path)

    output_dir = tmp_path / "certs_out"
    output_dir.mkdir()

    state = AppState()
    state.template_path = template_path
    state.template_width = 600
    state.template_height = 400
    state.output_folder = output_dir

    # 3 columns: ID, Name, Contact
    state.headers = ["ID", "Name", "Contact"]
    state.raw_data = [
        {"ID": "EMP-001", "Name": "Alice Johnson", "Contact": "555-1111"},
        {"ID": "EMP-002", "Name": "Bob Miller", "Contact": ""},  # empty contact
    ]
    state.filename_column = "ID"

    # Enable ID and Name at distinct positions, with Contact enabled as well
    field_id = FieldConfig(
        column_name="ID",
        enabled=True,
        text_x=500.0,
        text_y=50.0,
        font_size=20,
        alignment="right",
        text_color="#FF0000",
    )
    field_name = FieldConfig(
        column_name="Name",
        enabled=True,
        text_x=300.0,
        text_y=200.0,
        font_size=36,
        alignment="center",
        text_color="#000000",
    )
    field_contact = FieldConfig(
        column_name="Contact",
        enabled=True,
        text_x=300.0,
        text_y=320.0,
        font_size=18,
        alignment="center",
        text_color="#0000FF",
    )

    state.fields = [field_id, field_name, field_contact]

    q = Queue()
    cancel_ev = Event()

    thread = GeneratorThread(state, q, cancel_ev)
    thread.run()

    # Files should be named after ID column (EMP-001.png, EMP-002.png)
    file1 = output_dir / "EMP-001.png"
    file2 = output_dir / "EMP-002.png"
    assert file1.exists()
    assert file2.exists()

    with Image.open(file1) as img1:
        assert img1.size == (600, 400)
        colors = img1.getcolors(maxcolors=600 * 400)
        assert len(colors) > 1

    with Image.open(file2) as img2:
        assert img2.size == (600, 400)


def test_field_selection_and_toggling():
    state = AppState(template_width=1000, template_height=800)
    state.headers = ["ID", "Name", "Role", "Date"]
    state.fields = [
        FieldConfig(column_name="ID", enabled=True, text_x=100, text_y=100),
        FieldConfig(column_name="Name", enabled=True, text_x=500, text_y=400),
        FieldConfig(column_name="Role", enabled=False, text_x=500, text_y=500),
        FieldConfig(column_name="Date", enabled=True, text_x=500, text_y=600),
    ]

    state.active_field_index = 1
    assert state.active_field.column_name == "Name"
    assert state.text_x == 500
    assert state.text_y == 400

    # Switch active field
    state.active_field_index = 0
    assert state.active_field.column_name == "ID"
    assert state.text_x == 100

    # Modify active field
    state.text_x = 150
    assert state.fields[0].text_x == 150
