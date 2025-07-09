from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget, QHeaderView, QSizePolicy, QDateEdit)
from PyQt5.QtCore import Qt, QDate
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class SalesUi(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.get_button_stylesheet = main_window.get_button_stylesheet
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        # Header
        header_layout = QHBoxLayout()
        title = QLabel("Sales Reports")
        title.setStyleSheet("font-size: 22px; font-weight: bold; margin-right: 24px;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        self.export_btn = QPushButton("Export CSV")
        self.export_btn.setMinimumHeight(40)
        self.export_btn.setStyleSheet(self.get_button_stylesheet())
        header_layout.addWidget(self.export_btn)
        layout.addLayout(header_layout)
        # Date range filter
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("From:"))
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDate(QDate.currentDate().addMonths(-1))
        filter_layout.addWidget(self.start_date_edit)
        filter_layout.addWidget(QLabel("To:"))
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDate(QDate.currentDate())
        filter_layout.addWidget(self.end_date_edit)
        self.filter_btn = QPushButton("Filter")
        self.filter_btn.setStyleSheet(self.get_button_stylesheet())
        filter_layout.addWidget(self.filter_btn)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        # Monthly sales table
        self.sales_table = QTableWidget()
        self.sales_table.setColumnCount(4)
        self.sales_table.setHorizontalHeaderLabels([
            "Month", "Total Sales", "Number of Bills", "Average Bill"
        ])
        self.sales_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.sales_table.setAlternatingRowColors(True)
        self.sales_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.sales_table)
        # Charts area
        self.figure = Figure(figsize=(6, 3))
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        self.setLayout(layout)
        self.filter_btn.clicked.connect(self.main_window.handle_sales_filter)

    def update_charts(self, sales_data):
        self.figure.clear()
        ax_bar = self.figure.add_subplot(211)
        ax_line = self.figure.add_subplot(212)
        # Prepare data
        months = [row[0] for row in sales_data]
        totals = []
        for row in sales_data:
            try:
                totals.append(float(row[1]))
            except Exception:
                totals.append(0)
        # Bar chart
        ax_bar.bar(months, totals, color='#1976d2')
        ax_bar.set_title('Monthly Sales (Bar Chart)')
        ax_bar.set_ylabel('Total Sales')
        ax_bar.set_xticklabels(months, rotation=30, ha='right')
        # Line chart
        ax_line.plot(months, totals, marker='o', color='#388e3c')
        ax_line.set_title('Monthly Sales (Line Chart)')
        ax_line.set_ylabel('Total Sales')
        ax_line.set_xticklabels(months, rotation=30, ha='right')
        self.figure.tight_layout()
        self.canvas.draw() 