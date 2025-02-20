/** @odoo-module **/

import { Component } from "@odoo/owl";

export class SignupValidation extends Component {
    setup() {
        this.setupEmailValidation();
    }

    setupEmailValidation() {
        const loginInput = document.querySelector('#login');
        if (loginInput) {
            loginInput.addEventListener('input', this.validateEmail);
        }
    }

    validateEmail(event) {
        const email = event.target.value.toLowerCase();
        const pattern = /^[a-zA-Z0-9._%+-]+@(gmail|hotmail|outlook|yahoo)\.com$/;
        
        if (!pattern.test(email)) {
            event.target.setCustomValidity('Use un correo de Gmail, Hotmail, Outlook o Yahoo');
        } else {
            event.target.setCustomValidity('');
        }
    }
}