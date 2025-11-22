{
    "name": "OCS Weight Master",
    "version": "19.0.1.0.0",
    "summary": "MQTT integration for XK3190-D10 / weighbridge streams",
    "category": "Operations/Inventory",
    "author": "OCS",
    "license": "LGPL-3",
    "depends": ["base", "web", "hr", "product"],
    "data": [
        "data/ir_sequence_data.xml",
        "data/transaction_type_data.xml",
        "reports/weighbridge_transaction_report.xml",
        "views/weight_record_views.xml",
        "views/transaction_type_views.xml",
        "views/driver_views.xml",
        "views/mqtt_latest_views.xml",
        "views/weighbridge_transaction_views.xml",
        "security/ir.model.access.csv"
    ],
    "assets": {
        "web.assets_backend": [
            "ocs_weight_master/static/src/js/mqtt_form_controller.js",
        ],
    },
    "installable": True,
    "application": True,
    "post_init_hook": "start_mqtt",
}