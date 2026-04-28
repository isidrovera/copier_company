/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Dialog } from "@web/core/dialog/dialog";
import { Component, useState, onMounted } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

class OneDriveSelector extends Component {
    setup() {
        this.orm = useService("orm");
        this.state = useState({
            files: [],
            stack: [],
        });

        onMounted(() => {
            this.loadRoot();
        });
    }

    async loadRoot() {
        const res = await this.orm.call(
            "onedrive.account",
            "list_files",
            [],
            {}
        );
        this.state.files = res.value || res;
        this.state.stack = [];
    }

    async openFolder(file) {
        const res = await this.orm.call(
            "onedrive.account",
            "list_files",
            [],
            { parent_id: file.id }
        );
        this.state.files = res.value || res;
        this.state.stack.push(file);
    }

    async goBack() {
        this.state.stack.pop();
        if (this.state.stack.length === 0) {
            return this.loadRoot();
        }
        const last = this.state.stack[this.state.stack.length - 1];
        return this.openFolder(last);
    }

    async selectFile(file) {
        if (file.folder) {
            return this.openFolder(file);
        }

        await this.orm.call(
            "account.move.send.wizard",
            "action_attach_onedrive_file",
            [this.props.wizard_id],
            { item_id: file.id }
        );

        this.props.close();
    }
}

OneDriveSelector.template = "onedrive_selector.Template";

registry.category("actions").add("onedrive_selector_dialog", (env, action) => {
    env.services.dialog.add(OneDriveSelector, {
        wizard_id: action.params.wizard_id,
    });
});