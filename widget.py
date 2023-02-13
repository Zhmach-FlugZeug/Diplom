# This Python file uses the following encoding: utf-8
import sys

from PySide6.QtWidgets import QWidget, QFileDialog, QMessageBox, QApplication


# Important:
# You need to run the following command to generate the ui_form.py file
#     pyside6-uic form.ui -o ui_form.py, or
#     pyside2-uic form.ui -o ui_form.py
from ui_form import Ui_Widget

class Widget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.ui = Ui_Widget()
        self.ui.setupUi(self)
        self.ui.call_conv.addItem("ms64")
        self.ui.call_conv.addItem("fastcall")
        self.ui.call_conv.addItem("stdcall")
        self.ui.call_conv.addItem("thiscall")



    """def browsedirs(self):
        dir_name = QFileDialog.getExistingDirectory(self)

        print(self.ui.out_button.sender())
        if self.ui.out_button.sender():
            print("out_button clicked")
            self.ui.output_dir.setText(dir_name)
            pass
        elif self.ui.in_button.sender():
            print("in_button clicked")
            self.ui.input_dir.setText(dir_name)
            pass
        elif self.ui.drio_button.sender():
            print("drio_button clicked")
            self.ui.drio_dir.setText(dir_name)
            pass
        elif self.ui.dict_button.sender():
            print("dict_button clicked")
            self.ui.dict_dir.setText(dir_name)
            pass

        if self.ui.input_dir.text() == self.ui.output_dir.text():
            QMessageBox.about(self, 'Error', "Input directory and output directory can't be same")
            return None"""

    def on_trg_button_clicked(self):
        fname = QFileDialog.getOpenFileName(self, 'Open file', '', 'Binaries (*.exe *.dll)')
        print(fname)
        if fname[0] == "":
            return None
        else:
            self.ui.trg_module.setText(fname[0])


    def on_dict_button_clicked(self):
        dir_name = QFileDialog.getExistingDirectory(self)
        if dir_name == "":
            return None
        else:
            self.ui.dict_dir.setText(dir_name)


    def on_drio_button_clicked(self):
        dir_name = QFileDialog.getExistingDirectory(self)
        if dir_name == "":
            return None
        else:
            self.ui.drio_dir.setText(dir_name)


    def on_out_button_clicked(self):
        dir_name = QFileDialog.getExistingDirectory(self)
        if dir_name == "":
            return None
        else:
            self.ui.output_dir.setText(dir_name)

        if self.ui.input_dir.text() == self.ui.output_dir.text():
            QMessageBox.about(self, 'Error', "Input directory and output directory can't be same")


    def on_in_button_clicked(self):
        dir_name = QFileDialog.getExistingDirectory(self)
        if dir_name == "":
            return None
        else:
            self.ui.input_dir.setText(dir_name)

        if self.ui.input_dir.text() == self.ui.output_dir.text():
            QMessageBox.about(self, 'Error', "Input directory and output directory can't be same")



    def on_distrib_mode_clicked(self):
        if self.ui.fuzz_id.isEnabled():
            self.ui.fuzz_id.setDisabled(True)
        else:
            self.ui.fuzz_id.setEnabled(True)
        pass


    def on_dbg_mode_clicked(self):
        if self.ui.log_button.isEnabled() and self.ui.log_dir.isEnabled():
            self.ui.log_button.setDisabled(True)
            self.ui.log_dir.setDisabled(True)
            pass
        else:
            self.ui.log_button.setEnabled(True)
            self.ui.log_dir.setEnabled(True)
            pass
        pass


    def on_outf_button_clicked(self):
        fname = QFileDialog.getOpenFileName(self, 'Open file')
        print(fname)
        if fname[0] == "":
            return None
        else:
            self.ui.out_file.setText(fname[0])
        pass


    def on_dumb_clicked(self):
        if self.ui.call_conv.isEnabled():
            self.ui.cov_module.setDisabled(True)
            self.ui.cov_button.setDisabled(True)
            self.ui.trg_module.setDisabled(True)
            self.ui.trg_button.setDisabled(True)
            self.ui.rva.setDisabled(True)
            self.ui.fuzz_iter.setDisabled(True)
            self.ui.args.setDisabled(True)
            self.ui.call_conv.setDisabled(True)
            self.ui.cov_module.setDisabled(True)
            self.ui.drio_dir.setDisabled(True)
            self.ui.dbg_checkbox.setDisabled(True)
        else:
            self.ui.cov_module.setEnabled(True)
            self.ui.cov_button.setEnabled(True)
            self.ui.trg_module.setEnabled(True)
            self.ui.trg_button.setEnabled(True)
            self.ui.rva.setEnabled(True)
            self.ui.fuzz_iter.setEnabled(True)
            self.ui.args.setEnabled(True)
            self.ui.call_conv.setEnabled(True)
            self.ui.cov_module.setEnabled(True)
            self.ui.drio_dir.setEnabled(True)
            self.ui.dbg_checkbox.setEnabled(True)

        pass


if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = Widget()
    widget.show()
    widget.ui.in_button.clicked.connect(widget.on_in_button_clicked)
    widget.ui.out_button.clicked.connect(widget.on_out_button_clicked)
    widget.ui.drio_button.clicked.connect(widget.on_drio_button_clicked)
    widget.ui.dict_button.clicked.connect(widget.on_dict_button_clicked)
    widget.ui.trg_button.clicked.connect(widget.on_trg_button_clicked)
    widget.ui.distrib_mode.clicked.connect(widget.on_distrib_mode_clicked)
    widget.ui.dbg_checkbox.clicked.connect(widget.on_dbg_mode_clicked)
    widget.ui.dumb.clicked.connect(widget.on_dumb_clicked)
    sys.exit(app.exec())
