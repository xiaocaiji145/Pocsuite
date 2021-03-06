#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Copyright (c) 2014-2015 pocsuite developers (http://seebug.org)
See the file 'docs/COPYING' for copying permission
"""

import types
from pocsuite.thirdparty.requests.exceptions import ConnectTimeout
from pocsuite.lib.core.data import logger
from pocsuite.lib.core.enums import CUSTOM_LOGGING
from pocsuite.lib.core.enums import OUTPUT_STATUS
from pocsuite.lib.core.common import parseTargetUrl
from pocsuite.lib.core.data import kb
from pocsuite.lib.core.data import conf


class POCBase(object):

    def __init__(self):
        self.type = None
        self.target = None
        self.url = None
        self.mode = None
        self.params = None
        self.verbose = None

    def execute(self, target, headers=None, params=None, mode='verify', verbose=True):
        """
        :param url: the target url
        :param headers: a :class dict include some fields for request header.
        :param params: a instance of Params, includ extra params

        :return: A instance of Output
        """
        self.target = target
        self.url = parseTargetUrl(target)
        self.headers = headers
        self.params = params
        self.mode = mode
        self.verbose = verbose
        # TODO
        output = None

        try:
            if self.mode == 'attack':
                output = self._attack()
            else:
                output = self._verify()

        except NotImplementedError:
            logger.log(CUSTOM_LOGGING.ERROR, 'POC: %s not defined ' '%s mode' % (self.name, self.mode))
            output = Output(self)

        except ConnectTimeout, e:
            while conf.retry > 0:
                logger.log(CUSTOM_LOGGING.WARNING, 'POC: %s timeout, start it over.' % self.name)
                try:
                    if self.mode == 'attack':
                        output = self._attack()
                    else:
                        output = self._verify()
                    break
                except ConnectTimeout:
                    logger.log(CUSTOM_LOGGING.ERROR, 'POC: %s time-out retry failed!' % self.name)
                    output = Output(self)
                conf.retry -= 1
            else:
                logger.log(CUSTOM_LOGGING.ERROR, str(e))
                output = Output(self)

        except Exception, e:
            logger.log(CUSTOM_LOGGING.ERROR, str(e))
            output = Output(self)

        return output

    def _attack(self):
        ''' 
        @function   以Poc的attack模式对urls进行检测(可能具有危险性)
                    需要在用户自定义的Poc中进行重写
                    返回一个Output类实例
        '''
        raise NotImplementedError

    def _verify(self):
        '''
        @function   以Poc的verify模式对urls进行检测(可能具有危险性)
                    需要在用户自定义的Poc中进行重写
                    返回一个Output类实例
        '''
        raise NotImplementedError

    """
    def _kwargsPatch(self, func):
        def wrapper(*args, **kwargs):

            try:
                userHeaders = kwargs['headers']
            except:
                userHeaders = {}

            kwargs.update({'headers': self.headers})
            kwargs['headers'].update(userHeaders)
            return func(*args, **kwargs)
        return wrapper

    req.get = _kwargsPatch(req.get)
    """


class Output(object):

    ''' output of pocs
    Usage::
        >>> poc = POCBase()
        >>> output = Output(poc)
        >>> result = {'FileInfo': ''}
        >>> output.success(result)
        >>> output.fail('Some reason failed or errors')
    '''

    def __init__(self, poc=None):
        if poc:
            self.url = poc.url
            self.mode = poc.mode
            self.vulID = poc.vulID
            self.name = poc.name
            self.appName = poc.appName
            self.appVersion = poc.appVersion
        self.error = ""
        self.result = {}
        self.status = OUTPUT_STATUS.FAILED

    def is_success(self):
        return bool(True and self.status)

    def success(self, result):
        assert isinstance(result, types.DictType)
        self.status = OUTPUT_STATUS.SUCCESS
        self.result = result

    def fail(self, error):
        self.status = OUTPUT_STATUS.FAILED
        assert isinstance(error, types.StringType)
        self.error = error

    def show_result(self):
        if self.status == OUTPUT_STATUS.SUCCESS:
            infoMsg = "poc-%s '%s' has already been detected against '%s'." % (self.vulID, self.name, self.url)
            logger.log(CUSTOM_LOGGING.SUCCESS, infoMsg)
            for k, v in self.result.items():
                if isinstance(v, dict):
                    for kk, vv in v.items():
                        logger.log(CUSTOM_LOGGING.SUCCESS, "%s : %s" % (kk, vv))
                else:
                    logger.log(CUSTOM_LOGGING.SUCCESS, "%s : %s" % (k, v))
        else:
            errMsg = "poc-%s '%s' failed." % (self.vulID, self.name)
            logger.log(CUSTOM_LOGGING.ERROR, errMsg)
