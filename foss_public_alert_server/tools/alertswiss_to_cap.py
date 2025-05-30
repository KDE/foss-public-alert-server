# SPDX-FileCopyrightText: Volker Krause <vkrause@kde.org>
# SPDX-License-Identifier: AGPL-3.0-or-later

import json
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from lib import alertswiss, cap

with open(sys.argv[1]) as f:
    alerts = json.load(f)
for alert in alerts['alerts']:
    msg = cap.CAPAlertMessage()
    msg.xml = alertswiss.AlertSwiss.json_to_cap(alert)
    print(msg.to_string())
