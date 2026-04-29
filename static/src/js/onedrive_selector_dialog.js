/** @odoo-module **/

import { Component, useState, useSubEnv } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

// Ruta real: odoo_onedrive_integration/static/src/js/onedrive_app.js
import { OneDriveApp } from "@odoo_onedrive_integration/js/onedrive_app";


export class OneDriveSelectorDialog extends Component {
    static template = "odoo_onedrive_integration.OneDriveSelectorDialog";
    static components = { Dialog, OneDriveApp };
    static props = {
        wizard_id: { type: Number },
        move_id: { type: Number, optional: true },
        close: { type: Function },
    };

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");

        this.state = useState({
            selectedFiles: [],   // [{id, name}] acumulado entre carpetas
            attaching: false,
        });

        // Exponemos un "bus" sencillo para que OneDriveApp,
        // al estar en modo selector, nos avise de los cambios.
        useSubEnv({
            onedriveSelector: {
                mode: "select",
                onSelectionChange: (files) => this.onSelectionChange(files),
                getSelection: () => this.state.selectedFiles,
            },
        });
    }

    onSelectionChange(files) {
        this.state.selectedFiles = files;
    }

    get selectionCount() {
        return this.state.selectedFiles.length;
    }

    get canAttach() {
        return this.selectionCount > 0 && !this.state.attaching;
    }

    cancel() {
        this.props.close();
    }

    async attach() {
        if (!this.canAttach) return;
        this.state.attaching = true;
        const itemIds = this.state.selectedFiles.map((f) => f.id);
        try {
            const res = await this.orm.call(
                "account.move.send.wizard",
                "action_attach_onedrive_files",
                [[this.props.wizard_id], itemIds],
            );

            const okCount = (res.attachment_ids || []).length;
            const errCount = (res.errors || []).length;

            if (okCount > 0) {
                this.notification.add(
                    _t("%s archivo(s) adjuntado(s)", okCount),
                    { type: "success" },
                );
            }
            if (errCount > 0) {
                this.notification.add(
                    _t("%s error(es): %s", errCount, (res.errors || []).join(" · ")),
                    { type: "warning" },
                );
            }

            // Cerramos el diálogo. El wizard sigue abierto.
            this.props.close();

            // Notificación global para que el wizard refresque adjuntos.
            const ev = new CustomEvent("onedrive:attachments_added", {
                detail: { wizardId: this.props.wizard_id },
            });
            document.dispatchEvent(ev);
        } catch (e) {
            console.error("attach error:", e);
            this.notification.add(_t("Error al adjuntar"), { type: "danger" });
        } finally {
            this.state.attaching = false;
        }
    }
}


registry.category("actions").add(
    "onedrive_selector_dialog",
    (env, action) => {
        env.services.dialog.add(OneDriveSelectorDialog, {
            wizard_id: action.params.wizard_id,
            move_id: action.params.move_id,
        });
    },
);