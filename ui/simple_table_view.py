
# pylint: disable=no-name-in-module
from PyQt5.QtWidgets import QHeaderView, QTableView, QTableWidget

class SimpleTableView(QTableView):
    # pylint: disable=too-few-public-methods
    """Simple implementation of a QTableView"""

    def __init__(self, model, columns, **kwargs):
        super().__init__(**kwargs)

        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setSelectionMode(QTableView.SingleSelection)

        self.setShowGrid(False)
        self.setAlternatingRowColors(True)

        self.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.horizontalHeader().setStretchLastSection(False)
        self.horizontalHeader().setHighlightSections(False)

        self.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.verticalHeader().setDefaultSectionSize(24)
        self.verticalHeader().setHighlightSections(False)

        self.setModel(model)

        self.columns = columns
        for col_idx, col_spec in enumerate(self.columns):
            if col_spec is None:
                self.setColumnHidden(col_idx, True)
                continue

            self.setItemDelegateForColumn(col_idx, col_spec['delegate'])

            if 'width' in col_spec:
                self.horizontalHeader().resizeSection(col_idx, col_spec['width'])
            else:
                self.horizontalHeader().setSectionResizeMode(col_idx, QHeaderView.Stretch)
