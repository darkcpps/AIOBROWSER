from __future__ import annotations

from dataclasses import dataclass

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
)

from ui.core.styles import COLORS


@dataclass(frozen=True)
class TorrentFileEntry:
    index: int
    path: str
    size: int


def _format_bytes(value: int) -> str:
    size = float(max(0, int(value)))
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} PB"


class TorrentFileSelectorDialog(QDialog):
    def __init__(self, title: str, files: list[dict] | list[TorrentFileEntry], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Files to Download")
        self._title = title or "Torrent Download"
        self._files: list[TorrentFileEntry] = []
        for item in files or []:
            if isinstance(item, TorrentFileEntry):
                self._files.append(item)
            else:
                self._files.append(
                    TorrentFileEntry(
                        index=int(item.get("index", 0)),
                        path=str(item.get("path", "")),
                        size=int(item.get("size", 0)),
                    )
                )

        self._updating_checks = False
        self._selected_indices: list[int] = []
        self._node_cache: dict[tuple[str, ...], QTreeWidgetItem] = {}
        self._init_ui()
        self._build_tree()
        self._update_summary()

    def selected_file_indices(self) -> list[int]:
        return list(self._selected_indices)

    def _init_ui(self) -> None:
        self.setMinimumSize(720, 520)
        self.setStyleSheet(
            f"""
            QDialog {{
                background-color: {COLORS["bg_primary"]};
                border: 1px solid {COLORS["border"]};
                border-radius: 16px;
            }}
            QLabel {{
                color: {COLORS["text_primary"]};
            }}
            QLineEdit {{
                background-color: {COLORS["bg_secondary"]};
                border: 1px solid {COLORS["border"]};
                border-radius: 10px;
                padding: 10px 12px;
                color: {COLORS["text_primary"]};
            }}
            QTreeWidget {{
                background-color: {COLORS["bg_secondary"]};
                border: 1px solid {COLORS["border"]};
                border-radius: 12px;
                color: {COLORS["text_primary"]};
            }}
            QTreeWidget::item {{
                padding: 6px 6px;
            }}
            QTreeWidget::item:selected {{
                background-color: {COLORS["bg_card_hover"]};
            }}
            QPushButton {{
                border-radius: 10px;
                padding: 10px 12px;
                font-weight: 700;
            }}
            """
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 18)
        layout.setSpacing(12)

        header = QLabel(f"Choose what to download: {self._title}")
        header.setWordWrap(True)
        header.setStyleSheet("font-size: 15px; font-weight: 800;")
        layout.addWidget(header)

        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Filter files (e.g. .iso, setup, language)...")
        self.filter_input.textChanged.connect(self._apply_filter)
        layout.addWidget(self.filter_input)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["File", "Size"])
        self.tree.setColumnWidth(0, 520)
        self.tree.setUniformRowHeights(True)
        self.tree.itemChanged.connect(self._on_item_changed)
        layout.addWidget(self.tree, 1)

        footer = QFrame()
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(0, 0, 0, 0)
        footer_layout.setSpacing(10)

        self.summary_label = QLabel("")
        self.summary_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px;")
        self.summary_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        footer_layout.addWidget(self.summary_label, 1)

        self.select_all_btn = QPushButton("Select all")
        self.select_all_btn.setStyleSheet(
            f"background-color: {COLORS['bg_card']}; color: {COLORS['text_primary']}; border: 1px solid {COLORS['border']};"
        )
        self.select_all_btn.clicked.connect(lambda: self._set_all_checks(Qt.CheckState.Checked))
        footer_layout.addWidget(self.select_all_btn)

        self.select_none_btn = QPushButton("Select none")
        self.select_none_btn.setStyleSheet(
            f"background-color: {COLORS['bg_card']}; color: {COLORS['text_primary']}; border: 1px solid {COLORS['border']};"
        )
        self.select_none_btn.clicked.connect(lambda: self._set_all_checks(Qt.CheckState.Unchecked))
        footer_layout.addWidget(self.select_none_btn)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setStyleSheet(
            f"background-color: {COLORS['bg_card']}; color: {COLORS['text_primary']}; border: 1px solid {COLORS['border']};"
        )
        self.cancel_btn.clicked.connect(self.reject)
        footer_layout.addWidget(self.cancel_btn)

        self.ok_btn = QPushButton("Download selected")
        self.ok_btn.setStyleSheet(
            f"background-color: {COLORS['accent_green']}; color: white; border: none;"
        )
        self.ok_btn.clicked.connect(self._accept_if_any_selected)
        footer_layout.addWidget(self.ok_btn)

        layout.addWidget(footer)

    def _build_tree(self) -> None:
        self.tree.clear()
        self._node_cache.clear()

        self._updating_checks = True
        try:
            for entry in sorted(self._files, key=lambda e: e.path.lower()):
                parts = [p for p in str(entry.path).replace("\\", "/").split("/") if p]
                if not parts:
                    parts = [f"file_{entry.index}"]

                parent_item = None
                for depth in range(len(parts) - 1):
                    key = tuple(parts[: depth + 1])
                    folder_name = parts[depth]
                    node = self._node_cache.get(key)
                    if node is None:
                        node = QTreeWidgetItem([folder_name, ""])
                        node.setFlags(node.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                        node.setCheckState(0, Qt.CheckState.Checked)
                        if parent_item is None:
                            self.tree.addTopLevelItem(node)
                        else:
                            parent_item.addChild(node)
                        self._node_cache[key] = node
                    parent_item = node

                leaf_name = parts[-1]
                leaf = QTreeWidgetItem([leaf_name, _format_bytes(entry.size)])
                leaf.setFlags(leaf.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                leaf.setCheckState(0, Qt.CheckState.Checked)
                leaf.setData(0, Qt.ItemDataRole.UserRole, int(entry.index))
                leaf.setData(1, Qt.ItemDataRole.UserRole, int(entry.size))
                if parent_item is None:
                    self.tree.addTopLevelItem(leaf)
                else:
                    parent_item.addChild(leaf)

            for i in range(self.tree.topLevelItemCount()):
                self.tree.topLevelItem(i).setExpanded(True)
        finally:
            self._updating_checks = False

    def _set_all_checks(self, state: Qt.CheckState) -> None:
        self._updating_checks = True
        try:
            for i in range(self.tree.topLevelItemCount()):
                item = self.tree.topLevelItem(i)
                item.setCheckState(0, state)
                self._propagate_to_children(item, state)
        finally:
            self._updating_checks = False
        self._update_summary()

    def _accept_if_any_selected(self) -> None:
        self._update_summary()
        if self._selected_indices:
            self.accept()
        else:
            self.summary_label.setText("Select at least one file to continue.")

    def _apply_filter(self, text: str) -> None:
        query = (text or "").strip().lower()
        if not query:
            for i in range(self.tree.topLevelItemCount()):
                self._set_visible_recursive(self.tree.topLevelItem(i), True)
            return

        for i in range(self.tree.topLevelItemCount()):
            self._apply_filter_recursive(self.tree.topLevelItem(i), query)

    def _apply_filter_recursive(self, item: QTreeWidgetItem, query: str) -> bool:
        visible = False
        if item.childCount() == 0:
            name = (item.text(0) or "").lower()
            visible = query in name
            item.setHidden(not visible)
            return visible

        any_child_visible = False
        for i in range(item.childCount()):
            if self._apply_filter_recursive(item.child(i), query):
                any_child_visible = True
        item.setHidden(not any_child_visible)
        return any_child_visible

    def _set_visible_recursive(self, item: QTreeWidgetItem, visible: bool) -> None:
        item.setHidden(not visible)
        for i in range(item.childCount()):
            self._set_visible_recursive(item.child(i), visible)

    def _on_item_changed(self, item: QTreeWidgetItem, column: int) -> None:
        if self._updating_checks or column != 0:
            return

        self._updating_checks = True
        try:
            state = item.checkState(0)
            self._propagate_to_children(item, state)
            self._update_parent_states(item)
        finally:
            self._updating_checks = False

        self._update_summary()

    def _propagate_to_children(self, item: QTreeWidgetItem, state: Qt.CheckState) -> None:
        for i in range(item.childCount()):
            child = item.child(i)
            child.setCheckState(0, state)
            self._propagate_to_children(child, state)

    def _update_parent_states(self, item: QTreeWidgetItem) -> None:
        parent = item.parent()
        if parent is None:
            return

        checked = 0
        unchecked = 0
        partial = 0
        for i in range(parent.childCount()):
            st = parent.child(i).checkState(0)
            if st == Qt.CheckState.Checked:
                checked += 1
            elif st == Qt.CheckState.Unchecked:
                unchecked += 1
            else:
                partial += 1

        if partial > 0:
            parent.setCheckState(0, Qt.CheckState.PartiallyChecked)
        else:
            if checked == parent.childCount():
                parent.setCheckState(0, Qt.CheckState.Checked)
            elif unchecked == parent.childCount():
                parent.setCheckState(0, Qt.CheckState.Unchecked)
            else:
                parent.setCheckState(0, Qt.CheckState.PartiallyChecked)

        self._update_parent_states(parent)

    def _iter_leaf_items(self) -> list[QTreeWidgetItem]:
        leaves: list[QTreeWidgetItem] = []

        def walk(node: QTreeWidgetItem) -> None:
            if node.childCount() == 0:
                leaves.append(node)
                return
            for j in range(node.childCount()):
                walk(node.child(j))

        for i in range(self.tree.topLevelItemCount()):
            walk(self.tree.topLevelItem(i))
        return leaves

    def _update_summary(self) -> None:
        selected: list[int] = []
        selected_size = 0
        total_size = sum(int(x.size) for x in self._files)

        for leaf in self._iter_leaf_items():
            idx = leaf.data(0, Qt.ItemDataRole.UserRole)
            size = leaf.data(1, Qt.ItemDataRole.UserRole)
            if idx is None:
                continue
            if leaf.checkState(0) == Qt.CheckState.Checked:
                selected.append(int(idx))
                selected_size += int(size or 0)

        self._selected_indices = sorted(selected)
        self.summary_label.setText(
            f"Selected {len(selected)} / {len(self._files)} files • "
            f"{_format_bytes(selected_size)} selected • {_format_bytes(total_size)} total"
        )

