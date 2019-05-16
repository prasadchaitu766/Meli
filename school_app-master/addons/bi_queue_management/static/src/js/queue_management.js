odoo.define('bi_queue_management.queue_management.js', function (require) {
"use strict";

var core = require('web.core');
var KanbanRecord = require('web_kanban.Record');
var Model = require('web.Model');
var form_common = require('web.form_common');
var form_widget = require('web.form_widgets');

var QWeb = core.qweb;
var _t = core._t;



form_widget.WidgetButton.include({
    on_click:function() {
        if(this.node.attrs.custom === "print"){
        	
        	var name = this.view.ViewManager.action.xml_id;
        	var model =  this.view.ViewManager.action.res_model;
        	console.log(this);
        	this.do_action({
		      name: name,
           	  res_model: model,
              views: [[false, 'form']],
              type: 'ir.actions.act_window',
              view_type: "form",
              view_mode: "form",
        });
        	this.view.datarecord.name = '';
        	this.view.datarecord.phone = '';
        }
        else{
            this._super();
        }   
   
    }
   
	    
	});
	



});

