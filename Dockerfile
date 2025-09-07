FROM odoo:18.0

COPY addons/workplace_arm /mnt/extra-addons/workplace_arm

USER root
RUN chown -R odoo:odoo /mnt/extra-addons/
USER odoo

ENV ODOO_EXTRA_ADDONS=/mnt/extra-addons
