from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget, QHeaderView, QSizePolicy, QDateEdit, QFrame, QProgressDialog, QApplication, QDialog, QDialogButtonBox, QFormLayout, QTextEdit, QMenu, QTableWidgetItem)
from PyQt5.QtCore import Qt, QDate, QTimer
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from theme import theme_manager, create_animated_button
import logging
logger = logging.getLogger("medibit")

class SaleDetailsDialog(QDialog):
    def __init__(self, sale, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Sale Details - Order {getattr(sale, 'id', '')}")
        self.setMinimumWidth(500)
        layout = QFormLayout(self)
        layout.addRow("Order ID:", QLabel(str(getattr(sale, 'id', ''))))
        layout.addRow("Customer:", QLabel(getattr(sale, 'customer', '')))
        layout.addRow("Date:", QLabel(getattr(sale, 'timestamp', '')))
        layout.addRow("Total:", QLabel(f"₹{getattr(sale, 'total', 0):.2f}"))
        # Items
        items_text = QTextEdit()
        items_text.setReadOnly(True)
        items = getattr(sale, 'items', [])
        if hasattr(sale, 'items') and sale.items:
            items_text.setText("\n".join([
                f"{item.name} x{item.quantity} @ ₹{item.price:.2f} = ₹{item.subtotal:.2f}" for item in sale.items
            ]))
        else:
            items_text.setText("No items found.")
        layout.addRow("Items:", items_text)
        btns = QDialogButtonBox(QDialogButtonBox.Ok)
        btns.button(QDialogButtonBox.Ok).setText("Close")
        btns.setCenterButtons(True)
        btns.accepted.connect(self.accept)
        layout.addWidget(btns)
        self.setAccessibleName("Sale Details Dialog")
        self.setFocusPolicy(Qt.StrongFocus)

class SalesUi(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        logger.info("SalesUi initialized")
        self.init_ui()
        # Feedback banner
        self.feedback_banner = QLabel("")
        self.feedback_banner.setStyleSheet("padding: 8px; border-radius: 4px; font-weight: bold; font-size: 14px;")
        self.feedback_banner.setVisible(False)
        self.layout().insertWidget(0, self.feedback_banner)
        # Loading overlay
        self.loading_overlay = QProgressDialog("Please wait...", None, 0, 0, self)
        self.loading_overlay.setWindowModality(Qt.WindowModal)
        self.loading_overlay.setCancelButton(None)
        self.loading_overlay.setWindowTitle("Loading")
        self.loading_overlay.setMinimumDuration(0)
        self.loading_overlay.close()

    def show_loading(self, message="Loading..."):
        self.loading_overlay.setLabelText(message)
        self.loading_overlay.setValue(0)
        self.loading_overlay.show()
        QApplication.processEvents()

    def hide_loading(self):
        self.loading_overlay.hide()
        QApplication.processEvents()

    def show_banner(self, message, success=True):
        color = "#43a047" if success else "#e53935"
        self.feedback_banner.setStyleSheet(f"background: {color}; color: white; padding: 8px; border-radius: 4px; font-weight: bold; font-size: 14px;")
        self.feedback_banner.setText(message)
        self.feedback_banner.setVisible(True)
        QTimer.singleShot(3000, lambda: self.feedback_banner.setVisible(False))

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        # Header
        header_layout = QHBoxLayout()
        title = QLabel("Sales Reports")
        title.setStyleSheet("font-size: 22px; font-weight: bold; margin-right: 24px;")
        title.setToolTip("Section: Sales Reports")
        title.setAccessibleName("Sales Reports Title")
        header_layout.addWidget(title)
        header_layout.addStretch()
        # Date range pickers
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDate(QDate.currentDate().addMonths(-1))
        self.start_date_edit.setToolTip("Start date for sales filter.")
        self.start_date_edit.setAccessibleName("Start Date Picker")
        self.start_date_edit.setFocusPolicy(Qt.StrongFocus)
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDate(QDate.currentDate())
        self.end_date_edit.setToolTip("End date for sales filter.")
        self.end_date_edit.setAccessibleName("End Date Picker")
        self.end_date_edit.setFocusPolicy(Qt.StrongFocus)
        header_layout.addWidget(QLabel("From:"))
        header_layout.addWidget(self.start_date_edit)
        header_layout.addWidget(QLabel("To:"))
        header_layout.addWidget(self.end_date_edit)
        self.filter_btn = create_animated_button("Filter", self)
        self.filter_btn.setToolTip("Filter sales data by date range.")
        self.filter_btn.setAccessibleName("Filter Button")
        self.filter_btn.setFocusPolicy(Qt.StrongFocus)
        header_layout.addWidget(self.filter_btn)
        self.export_btn = create_animated_button("Export", self)
        self.export_btn.setToolTip("Export sales data as CSV file.")
        self.export_btn.setAccessibleName("Export CSV Button")
        self.export_btn.setFocusPolicy(Qt.StrongFocus)
        self.export_btn.clicked.connect(self.export_sales_data)
        header_layout.addWidget(self.export_btn)
        layout.addLayout(header_layout)
        # Connect filter
        self.filter_btn.clicked.connect(self.on_filter_clicked)
        self.start_date_edit.dateChanged.connect(self.on_filter_clicked)
        self.end_date_edit.dateChanged.connect(self.on_filter_clicked)
        # Sales Summary
        summary_frame = QFrame()
        summary_layout = QVBoxLayout(summary_frame)
        summary_layout.setContentsMargins(12, 12, 12, 12)
        summary_layout.setSpacing(10)
        summary_title = QLabel("Sales Summary")
        summary_title.setStyleSheet(theme_manager.get_section_title_stylesheet())
        summary_title.setToolTip("Section: Sales Summary")
        summary_title.setAccessibleName("Sales Summary Title")
        summary_layout.addWidget(summary_title)
        # Summary metrics
        metrics_layout = QHBoxLayout()
        self.total_sales_label = QLabel("Total Sales: $0.00")
        self.total_sales_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.total_sales_label.setToolTip("Total sales amount for the selected period.")
        self.total_sales_label.setAccessibleName("Total Sales Label")
        metrics_layout.addWidget(self.total_sales_label)
        self.total_orders_label = QLabel("Total Orders: 0")
        self.total_orders_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.total_orders_label.setToolTip("Total number of orders for the selected period.")
        self.total_orders_label.setAccessibleName("Total Orders Label")
        metrics_layout.addWidget(self.total_orders_label)
        self.avg_order_label = QLabel("Average Order: $0.00")
        self.avg_order_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.avg_order_label.setToolTip("Average order value for the selected period.")
        self.avg_order_label.setAccessibleName("Average Order Label")
        metrics_layout.addWidget(self.avg_order_label)
        metrics_layout.addStretch()
        summary_layout.addLayout(metrics_layout)
        layout.addWidget(summary_frame)
        # Sales Chart
        chart_frame = QFrame()
        chart_layout = QVBoxLayout(chart_frame)
        chart_layout.setContentsMargins(12, 12, 12, 12)
        chart_layout.setSpacing(10)
        chart_title = QLabel("Sales Chart")
        chart_title.setStyleSheet(theme_manager.get_section_title_stylesheet())
        chart_title.setToolTip("Section: Sales Chart")
        chart_title.setAccessibleName("Sales Chart Title")
        chart_layout.addWidget(chart_title)
        # Matplotlib chart
        self.figure = Figure(figsize=(6, 4))
        self.canvas = FigureCanvas(self.figure)
        chart_layout.addWidget(self.canvas)
        layout.addWidget(chart_frame)
        # Sales Table
        table_frame = QFrame()
        table_layout = QVBoxLayout(table_frame)
        table_layout.setContentsMargins(12, 12, 12, 12)
        table_layout.setSpacing(10)
        table_title = QLabel("Recent Sales")
        table_title.setStyleSheet(theme_manager.get_section_title_stylesheet())
        table_title.setToolTip("Section: Recent Sales")
        table_title.setAccessibleName("Recent Sales Title")
        table_layout.addWidget(table_title)
        self.sales_table = QTableWidget(0, 5)
        self.sales_table.setHorizontalHeaderLabels([
            "Order ID", "Customer", "Date", "Items", "Total"
        ])
        self.sales_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.sales_table.setStyleSheet(theme_manager.get_table_stylesheet())
        self.sales_table.setToolTip("Table showing recent sales transactions.")
        self.sales_table.setAccessibleName("Sales Table")
        self.sales_table.setProperty("aria-role", "table")
        self.sales_table.setFocusPolicy(Qt.StrongFocus)
        self.sales_table.setTabKeyNavigation(True)
        self.sales_table.itemSelectionChanged.connect(self.on_sale_selected)
        self.sales_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.sales_table.customContextMenuRequested.connect(self.show_context_menu)
        table_layout.addWidget(self.sales_table)
        # Pagination controls
        self.page_size = 20
        self.current_page = 0
        pagination_layout = QHBoxLayout()
        self.prev_page_btn = create_animated_button("Previous", self)
        self.prev_page_btn.setAccessibleName("Previous Page Button")
        self.prev_page_btn.setFocusPolicy(Qt.StrongFocus)
        self.prev_page_btn.clicked.connect(self.prev_page)
        self.next_page_btn = create_animated_button("Next", self)
        self.next_page_btn.setAccessibleName("Next Page Button")
        self.next_page_btn.setFocusPolicy(Qt.StrongFocus)
        self.next_page_btn.clicked.connect(self.next_page)
        self.page_label = QLabel("")
        pagination_layout.addWidget(self.prev_page_btn)
        pagination_layout.addWidget(self.page_label)
        pagination_layout.addWidget(self.next_page_btn)
        table_layout.addLayout(pagination_layout)
        # Table action buttons
        table_btn_layout = QHBoxLayout()
        self.view_sale_btn = create_animated_button("View Sale", self)
        self.view_sale_btn.setToolTip("View details of the selected sale.")
        self.view_sale_btn.setAccessibleName("View Sale Button")
        self.view_sale_btn.setFocusPolicy(Qt.StrongFocus)
        self.view_sale_btn.clicked.connect(self.view_sale)
        self.print_receipt_btn = QPushButton("Print Receipt")
        self.print_receipt_btn.setStyleSheet(theme_manager.get_button_stylesheet())
        self.print_receipt_btn.setToolTip("Print receipt for the selected sale.")
        self.print_receipt_btn.setAccessibleName("Print Receipt Button")
        self.print_receipt_btn.setFocusPolicy(Qt.StrongFocus)
        self.print_receipt_btn.clicked.connect(self.print_receipt)
        table_btn_layout.addWidget(self.view_sale_btn)
        table_btn_layout.addWidget(self.print_receipt_btn)
        table_btn_layout.addStretch()
        table_layout.addLayout(table_btn_layout)
        layout.addWidget(table_frame)
        # Load initial data
        self.load_sales_data()

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

    def export_sales_data(self):
        logger.info("Export CSV button clicked.")
        self.show_loading("Exporting sales data...")
        try:
            # ... existing code ...
            self.show_banner("Sales data exported.", success=True)
        except Exception as e:
            self.show_banner(f"Failed to export sales data: {str(e)}", success=False)
        finally:
            self.hide_loading()
        logger.info("Sales data exported.")
    def view_sale(self):
        logger.info("View Sale button clicked.")
        row = self.sales_table.currentRow()
        if row < 0:
            self.show_banner("No sale selected.", success=False)
            return
        sale_id = self.sales_table.item(row, 0).text()
        # Fetch sale object from service or DB
        sale = self.main_window.billing_service.get_bill_by_id(sale_id) if hasattr(self.main_window.billing_service, 'get_bill_by_id') else None
        if not sale:
            self.show_banner("Sale not found.", success=False)
            return
        dialog = SaleDetailsDialog(sale, self)
        dialog.exec_()
        logger.info("Sale viewed.")
    def print_receipt(self):
        logger.info("Print Receipt button clicked.")
        # ... existing code ...
        logger.info("Receipt printed.")

    def on_sale_selected(self):
        pass

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.load_sales_data()
    def next_page(self):
        self.current_page += 1
        self.load_sales_data()
    def load_sales_data(self):
        # Fetch all sales (bills) from the service
        sales = self.main_window.billing_service.get_recent_bills(1000) if hasattr(self.main_window.billing_service, 'get_recent_bills') else []
        # Pagination
        total_sales = len(sales)
        start = self.current_page * self.page_size
        end = start + self.page_size
        paged_sales = sales[start:end]
        self.sales_table.setRowCount(len(paged_sales))
        for row, sale in enumerate(paged_sales):
            self.sales_table.setItem(row, 0, QTableWidgetItem(str(getattr(sale, 'id', ''))))
            self.sales_table.setItem(row, 1, QTableWidgetItem(getattr(sale, 'customer', '')))
            self.sales_table.setItem(row, 2, QTableWidgetItem(getattr(sale, 'timestamp', '')))
            items = ", ".join([item.name for item in getattr(sale, 'items', [])]) if hasattr(sale, 'items') else ""
            self.sales_table.setItem(row, 3, QTableWidgetItem(items))
            self.sales_table.setItem(row, 4, QTableWidgetItem(f"₹{getattr(sale, 'total', 0):.2f}"))
        # Update pagination label and button states
        total_pages = max(1, (total_sales + self.page_size - 1) // self.page_size)
        self.page_label.setText(f"Page {self.current_page + 1} of {total_pages}")
        self.prev_page_btn.setEnabled(self.current_page > 0)
        self.next_page_btn.setEnabled((self.current_page + 1) * self.page_size < total_sales)

    def on_filter_clicked(self):
        if hasattr(self.main_window, 'handle_sales_filter'):
            self.main_window.handle_sales_filter()

    def show_context_menu(self, pos):
        menu = QMenu(self)
        view_action = menu.addAction("View Sale")
        print_action = menu.addAction("Print Receipt")
        export_action = menu.addAction("Export Sale")
        action = menu.exec_(self.sales_table.viewport().mapToGlobal(pos))
        row = self.sales_table.currentRow()
        if row < 0:
            return
        if action == view_action:
            self.view_sale()
        elif action == print_action:
            self.print_receipt()
        elif action == export_action:
            self.export_selected_sale(row)
    def export_selected_sale(self, row):
        # Placeholder for exporting a single sale
        sale_id = self.sales_table.item(row, 0).text()
        self.show_banner(f"Exported sale {sale_id} (placeholder)", success=True) 