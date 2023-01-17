odoo.define('import_movements.tree_button', function (require) {
    "use strict";
    var ListController = require('web.ListController');
    var ListView = require('web.ListView');
    var viewRegistry = require('web.view_registry');
    var TreeButton = ListController.extend({
        buttons_template: 'import_source_movement.buttons',
        events: _.extend({}, ListController.prototype.events, {
            'click .import_source_movement_wizard': '_OpenWizardMovements',
        }),
        _OpenWizardMovements: function () {
            var self = this;
            var default_type = '';
            switch(self.modelName) {
                case 'xepelin.movement.rsm':
                    default_type = 'rsm';
                    break;
                case 'xepelin.movement.spei':
                    default_type = 'spei';
                    break;
                case 'xepelin.movement.cfdi':
                    default_type = 'cfdi';
                    break;
                case 'xepelin.movement.bnc':
                    default_type = 'bnc';
                    break;
            };
            this.do_action({
                type: 'ir.actions.act_window',
                res_model: 'import.source.movement.wizard',
                name: `Import ${default_type.toUpperCase()}`,
                view_mode: 'form',
                view_type: 'form',
                views: [[false, 'form']],
                target: 'new',
                res_id: false,
                context: {
                    'default_type': default_type
                }
            });
        }
    });
    var ImportListView = ListView.extend({
        config: _.extend({}, ListView.prototype.config, {
            Controller: TreeButton,
        }),
    });
    viewRegistry.add('import_source_movement_button', ImportListView);
});