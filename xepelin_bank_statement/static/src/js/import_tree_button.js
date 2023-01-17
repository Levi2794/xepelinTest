odoo.define("import_bank_statement.tree_button", function (require) {
  "use strict";
  var ListController = require("web.ListController");
  var ListView = require("web.ListView");
  var viewRegistry = require("web.view_registry");
  var TreeButton = ListController.extend({
    buttons_template: "import_bank_statement.buttons",
    events: _.extend({}, ListController.prototype.events, {
      "click .import_bank_statement_wizard": "_OpenWizardImportBankStatement",
    }),
    _OpenWizardImportBankStatement: function () {
      var self = this;
      var default_type = "";
      var name = "";
      switch (self.modelName) {
        case "xepelin.bank.bci":
          default_type = "bci";
          name = "BCI";
          break;
        case "xepelin.bank.santander":
          default_type = "santander";
          name = "Santander";
          break;
      }
      this.do_action({
        type: "ir.actions.act_window",
        res_model: "import.bank.statement.wizard",
        name: `Import ${name} Bank`,
        view_mode: "form",
        view_type: "form",
        views: [[false, "form"]],
        target: "new",
        res_id: false,
        context: {
          default_type: default_type,
        },
      });
    },
  });
  var ImportListView = ListView.extend({
    config: _.extend({}, ListView.prototype.config, {
      Controller: TreeButton,
    }),
  });
  viewRegistry.add("import_bank_statement_button", ImportListView);
});
