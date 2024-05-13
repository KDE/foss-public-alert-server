import json
import re
import requests
import xml.etree.ElementTree as ET

from .abstract_CAP_parser import AbstractCAPParser


class MoWaSCapParser(AbstractCAPParser):

    def __init__(self, feed_url, source_id):
        super().__init__(feed_url, source_id)

    @staticmethod
    def convertProperty(xmlParent, mowasObj, propertyName):
        if not propertyName in mowasObj:
            return
        node = ET.SubElement(xmlParent, '{urn:oasis:names:tc:emergency:cap:1.2}' + propertyName)
        node.text = mowasObj[propertyName]

    @staticmethod
    def filterPolygon(polyData):
        # remove nonsense coordinates
        polyData = re.sub(r'-1.0,-1.0 ', '', polyData)
        # swap latitude/longitude pairs into the right order
        return re.sub(r'(-?\d+\.\d+),(-?\d+\.\d+)', r'\2,\1', polyData)

    def get_feed(self):
        req = requests.get(self.feed_url)  # @todo why not cached?
        feedData = json.loads(req.content)
        for alert in feedData:
            ET.register_namespace('', 'urn:oasis:names:tc:emergency:cap:1.2')
            root = ET.Element('{urn:oasis:names:tc:emergency:cap:1.2}alert')
            for prop in ['identifier', 'sender', 'sent', 'status', 'msgType', 'scope', 'note', 'references']:
                self.convertProperty(root, alert, prop)

            for alertInfo in alert['info']:
                info = ET.SubElement(root, '{urn:oasis:names:tc:emergency:cap:1.2}info',
                                     {'lang': alertInfo['language']})
                for category in alertInfo['category']:
                    cat = ET.SubElement(info, '{urn:oasis:names:tc:emergency:cap:1.2}category')
                    cat.text = category

                for prop in ['event', 'urgency', 'severity', 'certainty', 'headline', 'description', 'instruction',
                             'expires', 'web', 'contact']:
                    self.convertProperty(info, alertInfo, prop)

                for eventCode in alertInfo.get('eventCode', []):
                    eventCodeNode = ET.SubElement(info, '{urn:oasis:names:tc:emergency:cap:1.2}eventCode')
                    for prop in ['valueName', 'value']:
                        self.convertProperty(eventCodeNode, eventCode, prop)

                for param in alertInfo.get('parameter', []):
                    paramNode = ET.SubElement(info, '{urn:oasis:names:tc:emergency:cap:1.2}parameter')
                    for prop in ['valueName', 'value']:
                        self.convertProperty(paramNode, param, prop)
                    if param['valueName'] == 'sender_signature':
                        senderNameNode = ET.SubElement(info, '{urn:oasis:names:tc:emergency:cap:1.2}senderName')
                        senderNameNode.text = param['value']

                for area in alertInfo['area']:
                    areaNode = ET.SubElement(info, '{urn:oasis:names:tc:emergency:cap:1.2}area')
                    self.convertProperty(areaNode, area, 'areaDesc')
                    for poly in area['polygon']:
                        polyNode = ET.SubElement(areaNode, '{urn:oasis:names:tc:emergency:cap:1.2}polygon')
                        polyNode.text = self.filterPolygon(poly)
                    for code in area['geocode']:
                        codeNode = ET.SubElement(areaNode, '{urn:oasis:names:tc:emergency:cap:1.2}geocode')
                        for prop in ['valueName', 'value']:
                            self.convertProperty(codeNode, code, prop)
                    # TODO more area content

            self.addAlert(cap_data=ET.tostring(root, encoding='utf-8', xml_declaration=True).decode())
