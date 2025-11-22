/** @odoo-module **/

import { FormController } from "@web/views/form/form_controller";
import { registry } from "@web/core/registry";

export class MqttFormController extends FormController {
    setup() {
        super.setup();
        this.refreshInterval = null;
    }

    async onWillStart() {
        await super.onWillStart();
        // Ensure we load the latest record if no record is loaded
        if (!this.model.root.resId) {
            const latestRecords = await this.env.services.orm.searchRead(
                "weight.latest",
                [],
                ["id"],
                { limit: 1 }
            );
            if (latestRecords.length > 0) {
                await this.model.root.load({ resId: latestRecords[0].id });
            }
        }
        // Auto-refresh every 2 seconds
        this.startAutoRefresh();
    }

    onWillUnmount() {
        super.onWillUnmount();
        this.stopAutoRefresh();
    }

    startAutoRefresh() {
        this.stopAutoRefresh();
        this.refreshInterval = setInterval(async () => {
            try {
                // Get fresh data directly from server
                const latestRecords = await this.env.services.orm.searchRead(
                    "weight.latest",
                    [],
                    ["id", "weight", "timestamp"],
                    { limit: 1 }
                );
                
                if (latestRecords.length > 0) {
                    const latestRecord = latestRecords[0];
                    const latestRecordId = latestRecord.id;
                    const currentResId = this.model.root.resId;
                    
                    if (currentResId === latestRecordId) {
                        // Same record - update form fields directly
                        const record = this.model.root;
                        if (record) {
                            // Read fresh data from server
                            const freshData = await this.env.services.orm.read(
                                "weight.latest",
                                [latestRecordId],
                                ["weight", "timestamp"]
                            );
                            
                            if (freshData.length > 0) {
                                const newData = freshData[0];
                                
                                // Update the record data directly
                                if (record.data) {
                                    const oldWeight = record.data.weight;
                                    const oldTimestamp = record.data.timestamp;
                                    
                                    // Update if data changed
                                    if (newData.weight !== oldWeight || newData.timestamp !== oldTimestamp) {
                                        // Update fields directly
                                        record.update({
                                            weight: newData.weight,
                                            timestamp: newData.timestamp,
                                        });
                                    }
                                } else {
                                    // No data, reload
                                    await record.load({ resId: latestRecordId });
                                }
                            }
                        }
                    } else {
                        // Load the record (new or different)
                        await this.model.root.load({ resId: latestRecordId });
                    }
                }
            } catch (error) {
                console.error("Error refreshing MQTT form:", error);
            }
        }, 2000); // Refresh every 2 seconds
    }

    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }
}

MqttFormController.template = "web.FormView";

registry.category("views").add("mqtt_form", {
    ...registry.category("views").get("form"),
    Controller: MqttFormController,
});

