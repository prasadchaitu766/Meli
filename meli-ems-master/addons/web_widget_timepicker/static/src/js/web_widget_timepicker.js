odoo.define('web_widget_timepicker', function (require) {
    "use strict";

    var core = require('web.core');
    var formats = require('web.formats');
    var common = require('web.form_common');
    var Widget = require('web.Widget');
    var _t = core._t;
    var QWeb = core.qweb;

    var TimePickerField = common.AbstractField.extend(common.ReinitializeFieldMixin, {
        is_field_number: true,
        template: "TimePickerField",
        internal_format: 'float_time',
        widget_class: 'o_form_field_time',
        events: {
            'change input': 'store_dom_value',
        },
        init: function (field_manager, node) {
            this._super(field_manager, node);

            this.internal_set_value(0);

            this.options = _.defaults(this.options, {
                step: 15,
                selectOnBlur: true,
                timeFormat: 'H:i',
                // scrollDefault: 'now',
            });
        },
        initialize_content: function() {
            if(!this.get("effective_readonly")) {
                this.$el.find('input').timepicker(this.options);
                this.setupFocus(this.$('input'));
            }
        },
        is_syntax_valid: function() {
            if (!this.get("effective_readonly") && this.$("input").size() > 0) {
                try {
                    this.parse_value(this.$('input').val(), '');
                    return true;
                } catch(e) {
                    return false;
                }
            }
            return true;
        },
        is_false: function() {
            return this.get('value') === '' || this._super();
        },
        focus: function() {
            var input = this.$('input:first')[0];
            return input ? input.focus() : false;
        },
        set_dimensions: function (height, width) {
            this._super(height, width);
            this.$('input').css({
                height: height,
                width: width
            });
        },
        store_dom_value: function () {
            if (!this.get('effective_readonly')) {
                this.internal_set_value(
                    this.parse_value(
                        this.$('input').val(), ''));
            }
        },
        parse_value: function(val, def) {
            return formats.parse_value(val, {"widget": this.internal_format}, def);
        },
        format_value: function(val, def) {
            return formats.format_value(val, {"widget": this.internal_format}, def);
        },
        render_value: function() {
            var show_value = this.format_value(this.get('value'), '');

            if (!this.get("effective_readonly")) {
                this.$input = this.$el.find('input');
                this.$input.val(show_value);
            } else {
                this.$(".o_form_time_content").text(show_value);
            }
        },
    });

    core.form_widget_registry.add('timepicker', TimePickerField);


    var Timepicker = common.AbstractField.extend(common.ReinitializeFieldMixin, {

        template: "Timepicker",
        widget_class: 'o_form_field_time',
        events: {
            'change input': 'store_dom_value',
        },

        init: function () {
            this._super.apply(this, arguments);
            this.set("value", "");
            this.widget = this;
            this.defaultOptions = {
                disableTextInput: false,
                timeFormat: 'g:iA',
            }
        },
        initialize_content: function() {
            if(!this.get("effective_readonly")) {
                this.$el.find('input').timepicker(this.options);
                this.setupFocus(this.$('input'));
            }
        },

        store_dom_value: function () {

            if (!this.get('effective_readonly')) {
               // var selectedTime = $(e.currentTarget).timepicker('getTime');
                this.internal_set_value(this.$('input').val());
            }

        },
        is_false: function () {
            return this.get('value') === '' || this._super();
        },
        focus: function () {
            var input = this.$('input:first')[0];
            return input ? input.focus() : false;
        },
        set_dimensions: function (height, width) {
            this._super(height, width);
            this.$('input').css({
                height: height,
                width: width
            });
        },

        start: function() {
            this.options = _.extend(this.defaultOptions, this.options);

            this.on("change:effective_readonly", this, function() {
                this.display_field();
                this.render_value();
            });
            this.display_field();
            return this._super();
        },

        display_field: function() {
            this.$el.html(QWeb.render("Timepicker", {widget: this}));
        },

        render_value: function () {
            var selectedTime = this.get("value");
            var formatedTime = '';

            if (selectedTime) {
               // var d = new Date('1970-01-01 ' + this.get("value"));
                var d = this.get("value");
                formatedTime = d;
            }

            if (this.get('effective_readonly')) {
                this.$el.text(formatedTime);
            } else {
                this.$('input').timepicker(this.options);
                this.$('input').val(formatedTime);
            }
        }

    });
    core.form_widget_registry.add('odoo_timepicker', Timepicker);


    var TimePickerField2 = common.AbstractField.extend(common.ReinitializeFieldMixin, {
        is_field_number: true,
        template: "TimePickerField2",
        // internal_format: 'float_time',
        widget_class: 'o_form_field_time',
        events: {
            'change input': 'store_dom_value',
        },
        init: function (field_manager, node) {
            this._super(field_manager, node);

            this.internal_set_value(0);

            this.options = _.defaults(this.options, {
                step: 15,
                selectOnBlur: true,
                timeFormat: 'g:iA',
                // scrollDefault: 'now',
            });
        },
        initialize_content: function() {
            if(!this.get("effective_readonly")) {
                this.$el.find('input').timepicker(this.options);
                this.setupFocus(this.$('input'));
            }
        },
        is_syntax_valid: function() {
            if (!this.get("effective_readonly") && this.$("input").size() > 0) {
                try {
                    // this.parse_value(this.$('input').val(), '');
                    this.$('input').val();
                    return true;
                } catch(e) {
                    return false;
                }
            }
            return true;
        },
        is_false: function() {
            return this.get('value') === '' || this._super();
        },
        focus: function() {
            var input = this.$('input:first')[0];
            return input ? input.focus() : false;
        },
        set_dimensions: function (height, width) {
            this._super(height, width);
            this.$('input').css({
                height: height,
                width: width
            });
        },
        store_dom_value: function () {
            // if (!this.get('effective_readonly')) {
            //     this.internal_set_value(
            //         this.parse_value(
            //             this.$('input').val(), ''));
            // }
            if (!this.get('effective_readonly')) {
                this.internal_set_value(
                    
                        this.$('input').val(), '');
            }
        },
        parse_value: function(val, def) {
            return formats.parse_value(val, {"widget": this.internal_format}, def);
        },
        format_value: function(val, def) {
            return formats.format_value(val, {"widget": this.internal_format}, def);
        },
        render_value: function() {
            // var show_value = this.format_value(this.get('value'), '');
            var show_value = this.get('value') ? this.get('value') :'';
            

            if (!this.get("effective_readonly")) {
                this.$input = this.$el.find('input');
                this.$input.val(show_value);
            } else {
                this.$(".o_form_time_content").text(show_value);
            }
        },
    });

    core.form_widget_registry.add('timepicker2', TimePickerField2);

    return {
        TimePickerField: TimePickerField,
        Timepicker:Timepicker,
        TimePickerField2: TimePickerField2,
    };
});
