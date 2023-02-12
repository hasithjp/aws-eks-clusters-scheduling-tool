# layouts.py>
from h2o_wave import Q, ui


# Layout for startup window
def startup_layout(q: Q):
    q.page["meta"] = ui.meta_card(
        "startup",
        theme="h2o-dark",
        layouts=[
            ui.layout(
                breakpoint="xs",
                zones=[
                    ui.zone("startup_header"),
                    ui.zone(
                        name="space",
                        direction=ui.ZoneDirection.ROW,
                        size="100px"
                    ),
                    ui.zone(
                        name="startup_body",
                        direction=ui.ZoneDirection.ROW,
                        zones=[
                            ui.zone(
                                name="right",
                                zones=[
                                    ui.zone(
                                        "submission",
                                        direction=ui.ZoneDirection.COLUMN,
                                        wrap=ui.ZoneWrap.STRETCH,
                                        align="center",
                                    ),
                                ],
                            ),
                        ],
                    ),
                ],
            )
        ]
    )

    q.page['startup_header'] = ui.header_card(
        box='startup_header',
        title='Manage AWS EKS Clusters',
        subtitle='Stop/Start Clusters Using Schedules',
        image='https://wave.h2o.ai/img/h2o-logo.svg',
        color='card'
    )


# Layout for EKS table view
def main_layout(q: Q):
    q.page["meta"] = ui.meta_card(
        "main",
        theme="h2o-dark",
        layouts=[
            ui.layout(
                breakpoint="xs",
                zones=[
                    ui.zone("main_header"),
                    ui.zone(
                        name="main_body",
                        direction=ui.ZoneDirection.ROW,
                        zones=[
                            ui.zone(
                                name="main_right",
                                zones=[
                                    ui.zone("main_toolbar", direction=ui.ZoneDirection.ROW),
                                    ui.zone("main_title", direction=ui.ZoneDirection.ROW),
                                    ui.zone(
                                        "main_content",
                                        direction=ui.ZoneDirection.ROW,
                                        wrap=ui.ZoneWrap.STRETCH,
                                    ),
                                ],
                            ),
                        ],
                    ),
                ],
            )
        ]
    )

    q.page['main_header'] = ui.header_card(
        box='main_header',
        title='Manage AWS EKS Clusters',
        subtitle='Stop/Start Clusters Using Schedules',
        image='https://wave.h2o.ai/img/h2o-logo.svg',
        color='card',
        items=[ui.button(name='back_button', label='Back', primary=True)]
    )
