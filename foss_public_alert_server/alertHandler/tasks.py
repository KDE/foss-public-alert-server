# SPDX-FileCopyrightText: Nucleus <nucleus-ffm@posteo.de>
# SPDX-FileCopyrightText: Volker Krause <vkrause@kde.org>
# SPDX-License-Identifier: AGPL-3.0-or-later

from celery import shared_task

from .XML_CAP_parser import XMLCAPParser
from .MOWAS_CAP_parser import MoWaSCapParser
from .DWD_CAP_parser import DWDCAPParser
from time import sleep

feedReaders = [
    # interesting data, but past-only :(
    # CAPFeedReader('un-gdacs', 'https://gdacs.org/xml/gdacs_cap.xml'),

    MoWaSCapParser('de-mowas', 'https://warnung.bund.de/bbk.mowas/gefahrendurchsagen.json'),

    XMLCAPParser('af-andma', 'https://cap-sources.s3.amazonaws.com/af-andma-en/rss.xml'),
    XMLCAPParser('al-igewe', 'https://cap-sources.s3.amazonaws.com/al-igewe-en/rss.xml'),
    XMLCAPParser('ar-smn', 'https://ssl.smn.gob.ar/CAP/AR.php'),
    XMLCAPParser('at-meteoalarm', 'https://feeds.meteoalarm.org/feeds/meteoalarm-legacy-atom-austria'),
    XMLCAPParser('ba-meteoalarm', 'https://feeds.meteoalarm.org/feeds/meteoalarm-legacy-atom-bosnia-herzegovina'),
    # CAPFeedReader('bb-dem', 'https://brb-secondary.capews.com/capews/public/cap/ZGV7BH8QABtsUXcYRgx6QUd2enhTSA=='), # TODO no <area> data?
    XMLCAPParser('be-meteoalarm', 'https://feeds.meteoalarm.org/feeds/meteoalarm-legacy-atom-belgium'),
    XMLCAPParser('bg-meteoalarm', 'https://feeds.meteoalarm.org/feeds/meteoalarm-legacy-atom-bulgaria'),
    XMLCAPParser('br-inmet', 'https://apiprevmet3.inmet.gov.br/avisos/rss'),
    XMLCAPParser('bf-meteo', 'https://cap-sources.s3.amazonaws.com/bf-meteo-en/rss.xml'),
    XMLCAPParser('bw-met', 'https://cap-sources.s3.amazonaws.com/bw-met-en/rss.xml'),
    XMLCAPParser('ca-met-service', 'https://rss.naad-adna.pelmorex.com/'),
    XMLCAPParser('cd-mettelsat', 'https://cap-sources.s3.amazonaws.com/cd-mettelsat-en/rss.xml'),
    XMLCAPParser('cf-dmn', 'https://cap-sources.s3.amazonaws.com/cf-dmn-en/rss.xml'),
    XMLCAPParser('cg-anac', 'https://cap-sources.s3.amazonaws.com/cg-anac-en/rss.xml'),
    XMLCAPParser('ch-meteoalarm', 'https://feeds.meteoalarm.org/feeds/meteoalarm-legacy-atom-switzerland'),
    XMLCAPParser('ci-sodexam', 'https://cap-sources.s3.amazonaws.com/ci-sodexam-en/rss.xml'),
    XMLCAPParser('cm-meteo', 'https://cap-sources.s3.amazonaws.com/cm-meteo-en/rss.xml'),
    # CAPFeedReader('cn-cma', 'http://alert-feed.worldweather.org/cn-cma-xx/rss.xml'), # TODO needs boundary polygons for "CPEAS Geographic Code"
    XMLCAPParser('cr-imn', 'https://cap-sources.s3.amazonaws.com/cr-imn-en/rss.xml'),
    XMLCAPParser('cw-meteo', 'https://cap-sources.s3.amazonaws.com/cw-meteo-en/rss.xml'),
    XMLCAPParser('cy-meteoalarm', 'https://feeds.meteoalarm.org/feeds/meteoalarm-legacy-atom-cyprus'),
    XMLCAPParser('cz-meteoalarm', 'https://feeds.meteoalarm.org/feeds/meteoalarm-legacy-atom-czechia'),

    DWDCAPParser('de-dwd',
                  'https://opendata.dwd.de/weather/alerts/cap/COMMUNEUNION_EVENT_STAT/Z_CAP_C_EDZW_LATEST_PVW_STATUS_PREMIUMEVENT_COMMUNEUNION_MUL.zip'),
    MoWaSCapParser('de-lhp', 'https://warnung.bund.de/bbk.lhp/hochwassermeldungen.json'),


    XMLCAPParser('dk-meteoalarm', 'https://feeds.meteoalarm.org/feeds/meteoalarm-legacy-atom-denmark'),
    XMLCAPParser('dz-meteo', 'https://ametvigilance.meteo.dz/rss/rss_meteo_dz.xml'),
    XMLCAPParser('ec-inamhi', 'https://cap-sources.s3.amazonaws.com/ec-inamhi-es/rss.xml'),
    XMLCAPParser('ee-meteoalarm', 'https://feeds.meteoalarm.org/feeds/meteoalarm-legacy-atom-estonia'),
    XMLCAPParser('eg-ema', 'https://cap-sources.s3.amazonaws.com/eg-ema-en/rss.xml'),
    XMLCAPParser('es-meteoalarm', 'https://feeds.meteoalarm.org/feeds/meteoalarm-legacy-atom-spain'),
    XMLCAPParser('fi-meteoalarm', 'https://feeds.meteoalarm.org/feeds/meteoalarm-legacy-atom-finland'),
    XMLCAPParser('fr-meteoalarm', 'https://feeds.meteoalarm.org/feeds/meteoalarm-legacy-atom-france'),
    XMLCAPParser('ga-dgm', 'https://cap-sources.s3.amazonaws.com/ga-dgm-en/rss.xml'),
    XMLCAPParser('gb-meteoalarm', 'https://feeds.meteoalarm.org/feeds/meteoalarm-legacy-atom-united-kingdom'),
    XMLCAPParser('gm-dwr', 'https://cap-sources.s3.amazonaws.com/gm-dwr-en/rss.xml'),
    XMLCAPParser('gn-dnm', 'https://cap-sources.s3.amazonaws.com/gn-dnm-en/rss.xml'),
    XMLCAPParser('gr-meteoalarm', 'https://feeds.meteoalarm.org/feeds/meteoalarm-legacy-atom-greece'),
    XMLCAPParser('gw-inm', 'https://cap-sources.s3.amazonaws.com/gw-inm-fr/rss.xml'),
    XMLCAPParser('gy-hydromet', 'https://hydromet.gov.gy/cap/en/alerts/rss.xml'),
    XMLCAPParser('hk-weather', 'https://alerts.weather.gov.hk/V1/cap_atom.xml'),
    XMLCAPParser('hr-meteoalarm', 'https://feeds.meteoalarm.org/feeds/meteoalarm-legacy-atom-croatia'),
    XMLCAPParser('hu-meteoalarm', 'https://feeds.meteoalarm.org/feeds/meteoalarm-legacy-atom-hungary'),
    XMLCAPParser('id-bmkg', 'https://signature.bmkg.go.id/alert/public/en/rss.xml'),
    XMLCAPParser('ie-meteoalarm', 'https://feeds.meteoalarm.org/feeds/meteoalarm-legacy-atom-ireland'),
    XMLCAPParser('il-meteoalarm', 'https://feeds.meteoalarm.org/feeds/meteoalarm-legacy-atom-israel'),
    XMLCAPParser('in-imd', 'https://cap-sources.s3.amazonaws.com/in-imd-en/rss.xml'),
    XMLCAPParser('ir-irimo', 'https://cap-sources.s3.amazonaws.com/ir-irimo-en/rss.xml'),
    # CAPFeedReader('is-vedur', 'https://api.vedur.is/cap/v1/capbroker/active/category/Met/'), # TODO service not responding
    XMLCAPParser('it-meteoalarm', 'https://feeds.meteoalarm.org/feeds/meteoalarm-legacy-atom-italy'),
    XMLCAPParser('ja-meteo', 'https://alert.metservice.gov.jm/capfeed.php'),
    XMLCAPParser('ke-kmd', 'https://cap-sources.s3.amazonaws.com/ke-kmd-en/rss.xml'),
    XMLCAPParser('km-anacm', 'https://cap-sources.s3.amazonaws.com/km-anacm-en/rss.xml'),
    XMLCAPParser('kw-met', 'https://www.met.gov.kw/rss_eng/kuwait_cap.xml'),
    XMLCAPParser('ls-lms', 'https://cap-sources.s3.amazonaws.com/ls-lms-en/rss.xml'),
    XMLCAPParser('lt-meteoalarm', 'https://feeds.meteoalarm.org/feeds/meteoalarm-legacy-atom-lithuania'),
    XMLCAPParser('lu-meteoalarm', 'https://feeds.meteoalarm.org/feeds/meteoalarm-legacy-atom-luxembourg'),
    XMLCAPParser('lv-meteoalarm', 'https://feeds.meteoalarm.org/feeds/meteoalarm-legacy-atom-latvia'),
    XMLCAPParser('md-meteoalarm', 'https://feeds.meteoalarm.org/feeds/meteoalarm-legacy-atom-moldova'),
    XMLCAPParser('me-meteoalarm', 'https://feeds.meteoalarm.org/feeds/meteoalarm-legacy-atom-montenegro'),
    XMLCAPParser('mg-meteo', 'https://cap-sources.s3.amazonaws.com/mg-meteo-en/rss.xml'),
    XMLCAPParser('mk-meteoalarm',
                 'https://feeds.meteoalarm.org/feeds/meteoalarm-legacy-atom-republic-of-north-macedonia'),
    XMLCAPParser('ml-meteo', 'https://cap-sources.s3.amazonaws.com/ml-meteo-en/rss.xml'),
    # CAPFeedReader('mm-dmh', 'http://www.dmhwarning.gov.mm/eden/cap/public.rss'), # TODO server not responding
    XMLCAPParser('mn-namem', 'https://cap-sources.s3.amazonaws.com/mn-namem-en/rss.xml'),
    XMLCAPParser('mo-smg', 'https://rss.smg.gov.mo/cap_rss.xml'),
    XMLCAPParser('mt-meteoalarm', 'https://feeds.meteoalarm.org/feeds/meteoalarm-legacy-atom-malta'),
    XMLCAPParser('mu-mms', 'https://cap-sources.s3.amazonaws.com/mu-mms-en/rss.xml'),
    XMLCAPParser('mw-met', 'https://cap-sources.s3.amazonaws.com/mw-met-en/rss.xml'),
    XMLCAPParser('mx-smn', 'https://smn.conagua.gob.mx/tools/PHP/feedsmn/cap.php'),
    XMLCAPParser('ne-meteo', 'https://cap-sources.s3.amazonaws.com/ne-meteo-en/rss.xml'),
    XMLCAPParser('nl-meteoalarm', 'https://feeds.meteoalarm.org/feeds/meteoalarm-legacy-atom-netherlands'),
    XMLCAPParser('no-met', 'https://alert.met.no/alerts'),
    XMLCAPParser('nz-metservice', 'https://alerts.metservice.com/cap/rss'),
    XMLCAPParser('om-met', 'https://cap-sources.s3.amazonaws.com/om-met-en/rss.xml'),
    # CAPFeedReader('pg-pngmet', 'https://smartalert.pngmet.gov.pg/capfeed.php'), # TODO SSL certificate error
    XMLCAPParser('ph-pagasa', 'https://publicalert.pagasa.dost.gov.ph/feeds/'),
    XMLCAPParser('pl-meteoalarm', 'https://feeds.meteoalarm.org/feeds/meteoalarm-legacy-atom-poland'),
    XMLCAPParser('pt-meteoalarm', 'https://feeds.meteoalarm.org/feeds/meteoalarm-legacy-atom-portugal'),
    XMLCAPParser('py-dmh', 'https://cap-sources.s3.amazonaws.com/py-dmh-en/rss.xml'),
    XMLCAPParser('ro-meteoalarm', 'https://feeds.meteoalarm.org/feeds/meteoalarm-legacy-atom-romania'),
    XMLCAPParser('rs-meteoalarm', 'https://feeds.meteoalarm.org/feeds/meteoalarm-legacy-atom-serbia'),
    XMLCAPParser('ru-meteoinfo', 'https://meteoinfo.ru/hmc-output/cap/cap-feed/en/atom.xml'),
    # CAPFeedReader('sa-ncm', 'https://ncm.gov.sa/Ar/alert/Pages/feedalerts.aspx'), # TODO no polygons or geo codes?
    # CAPFeedReader('sb-met', 'https://smartalert.met.gov.sb/capfeed.php'), # TODO server no responding
    XMLCAPParser('sc-meteo', 'https://cap-sources.s3.amazonaws.com/sc-meteo-en/rss.xml'),
    XMLCAPParser('se-meteoalarm', 'https://feeds.meteoalarm.org/feeds/meteoalarm-legacy-atom-sweden'),
    XMLCAPParser('si-meteoalarm', 'https://feeds.meteoalarm.org/feeds/meteoalarm-legacy-atom-slovenia'),
    XMLCAPParser('sn-anacim', 'https://cap-sources.s3.amazonaws.com/sn-anacim-en/rss.xml'),
    XMLCAPParser('sk-meteoalarm', 'https://feeds.meteoalarm.org/feeds/meteoalarm-legacy-atom-slovakia'),
    XMLCAPParser('sr-meteo', 'https://cap-sources.s3.amazonaws.com/sr-meteo-en/rss.xml'),
    XMLCAPParser('sz-met', 'https://cap-sources.s3.amazonaws.com/sz-met-en/rss.xml'),
    XMLCAPParser('tg-dgmn', 'https://cap-sources.s3.amazonaws.com/tg-dgmn-en/rss.xml'),
    # CAPFeedReader('th-tmd', 'https://www.tmd.go.th/feeds/CAPfeeds.php'), # TODO needs ISO-3166-2 boundary polygons
    XMLCAPParser('tl-dnmg', 'https://cap-sources.s3.amazonaws.com/tl-dnmg-en/rss.xml'),
    XMLCAPParser('tn-meteo', 'https://cap-sources.s3.amazonaws.com/tn-meteo-en/rss.xml'),
    # CAPFeedReader('to-met', 'https://alerts.met.gov.to/capfeed.php'), # TODO SSL certificate error
    XMLCAPParser('tt-ttms', 'https://metproducts.gov.tt/ttms/public/api/feed?type=rss'),
    XMLCAPParser('tz-tma', 'https://cap-sources.s3.amazonaws.com/tz-tma-en/rss.xml'),
    XMLCAPParser('ug-unma', 'https://cap-sources.s3.amazonaws.com/ug-unma-en/rss.xml'),
    XMLCAPParser('us-nws', 'https://alerts.weather.gov/cap/us.php?x=0'),
    XMLCAPParser('us-nws-mz', 'https://alerts.weather.gov/cap/mzus.php?x=0'),
    XMLCAPParser('us-ntwc', 'https://www.tsunami.gov/events/xml/PAAQAtom.xml'),
    XMLCAPParser('us-ptwc', 'https://www.tsunami.gov/events/xml/PHEBAtom.xml'),
    XMLCAPParser('vg-bviddm', 'https://cap-sources.s3.amazonaws.com/uk-bviddm-en/rss.xml'),
    XMLCAPParser('vu-met', 'https://smartalert.vmgd.gov.vu/capfeed.php'),
    # CAPFeedReader('ws-samet', 'http://alert.samet.gov.ws/capfeed.php'), # TODO server not respondings
    XMLCAPParser('za-weathersa', 'https://caps.weathersa.co.za/Home/RssFeed'),
    XMLCAPParser('zw-msd', 'https://cap-sources.s3.amazonaws.com/zw-msd-en/rss.xml'),
]


@shared_task(name="fetch_alert_sources")
def fetch_alert_sources():
    print("fetching alert sources...")
    i = 0
    for feedReader in feedReaders:
        feedReader.get_feed()
        # if i > 10:
        #    break
        # i += 1
        break # @todo test only the first one, remove line to fetch all sources


@shared_task()
def test_celery():
    for i in range(0, 11):
        print(i)
        sleep(1)
    return "Task complete!"
