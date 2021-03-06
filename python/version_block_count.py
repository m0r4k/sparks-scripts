#!/usr/bin/env python3

import json
import subprocess
import sys
from pathlib import Path
from collections import OrderedDict
import datetime
import tempfile
import collections


class Coin:
    coin_cli = 'sparks-cli'
    tdir = tempfile.gettempdir()

    blocks_tmp = tdir + '/sparks_blocks.json'
    _now_ = int(datetime.datetime.now().strftime("%s"))

    argv_block_count = 999

    if len(sys.argv) > 1:
        argv_block_count = int(sys.argv[1]) - 1

    @classmethod
    def checkmnsync(cls):
        check = cls.clicmd('mnsync status')

        if not check['IsSynced']:
            print('you need to wait till mn is synced')
            quit()

        return True

    @classmethod
    def clicmd(cls, cmd, hook=''):
        if hook == 'string':
            cli_output = subprocess.check_output(cls.coin_cli + ' ' + cmd, shell=True).decode("utf-8")
            return cli_output

        try:
            cli_output = subprocess.check_output(
                cls.coin_cli + ' ' + cmd, shell=True).decode("utf-8")

            if hook == 'conf-hook':
                iter_num = 0
                output = ""
                iter_string = ""
                mnconf_json = {}
                # masternode list-conf INDEX HOOK makes name-ip json
                for i in cli_output.split('\"masternode\"'):
                    if iter_num != 0:
                        iter_string = '\"' + str(iter_num) + '\"'

                    output = "".join([output, iter_string + ' ' + i])
                    iter_num = iter_num + 1

                output_json = json.loads(output, object_pairs_hook=OrderedDict)

                for i in output_json:
                    mnconf_json[output_json[i]['alias']] = output_json[i]['address'].split(':')[
                        0]
                return mnconf_json

            cli_output = json.loads(cli_output, object_pairs_hook=OrderedDict)
            return cli_output
        except subprocess.CalledProcessError:
            quit()

    @classmethod
    def currentblock(cls, block=0):
        if block == 0:
            currentblock = cls.clicmd('getblockcount', "string")
        else:
            currentblock = block

        return int(currentblock)

    @classmethod
    def writefile(cls, filename, data, sort_keys=True, indent=4):
        Path(filename).write_text(json.dumps(data, sort_keys=sort_keys, indent=indent))
        return ()

    @staticmethod
    def openfile(filename):
        exists = Path(filename)
        if exists.is_file():
            _file = open(filename, 'r')
            _file_dic = json.load(_file, object_pairs_hook=OrderedDict)
            _file.close()
            return _file_dic
        return False

    @classmethod
    def loadblocks(cls, block_json, start_block, stop_block):

        while stop_block <= start_block:
            blockhash = cls.clicmd('getblockhash ' + str(stop_block), 'string')
            fullblock = cls.clicmd('getblock "' + blockhash + '" ')
            block_json[str(stop_block)] = fullblock
            stop_block = int(stop_block) + 1

        return block_json

    @classmethod
    def buildfiles(cls, start_block=0):
        cls.checkmnsync()
        block_json = {}
        block_count = cls.argv_block_count

        if start_block == 0:
            start_block = cls.currentblock(start_block)

        stop_block = start_block - block_count

        if cls.openfile(cls.blocks_tmp):
            block_json = cls.openfile(cls.blocks_tmp)
            _key = sorted(block_json.keys())
            _last_key = int(_key[-1])
            _first_key = int(_key[0])

            if _first_key != stop_block:
                block_json = cls.loadblocks(block_json, _first_key, stop_block)

            if _last_key != start_block:
                block_json = cls.loadblocks(block_json, start_block, _last_key)

        else:
            block_json = cls.loadblocks(block_json, start_block, stop_block)

        cls.writefile(cls.blocks_tmp, block_json)


    @classmethod
    def showstat(cls, blockcount=1000):
        def summation(collection):
            sum = 0
            for i in collection:
                sum = sum + collection[i]
            return sum

        stat_dict = cls.openfile(cls.blocks_tmp)
        _last_key = sorted(stat_dict.keys())[-1]

        start_block = int(_last_key) - int(cls.argv_block_count)

        cp_stat_dict = stat_dict.copy()
        for i in stat_dict:
            if int(i) < int(start_block):
                del cp_stat_dict[i]


        version_name = {'20000000': '20000000 old VersionBlock',
                        '20000008': '20000008 GN VersionBlock'}

        versionHex_list = []
        for i in cp_stat_dict:
            versionHex_list.append(cp_stat_dict[i]['versionHex'])

        count_versionHex = collections.Counter(versionHex_list)
        versionHex_sum = summation(count_versionHex)
        print(' ')
        print('{:<40s}'.format('MINED_BLOCKS [ blockheight = ' + _last_key + ']'), end='\n')
        print('{:=<40s}'.format(''), end='\n')

        for i in count_versionHex:

            if i in version_name:
                v_name = version_name[i]
            else:
                v_name = i + ' xxxx'

            print('{:<25s}'.format(v_name), end=': ')
            print('{:>5s}'.format(str(count_versionHex[i])), end=' ')
            print('{:>5s}'.format(str(int(round(count_versionHex[i] / versionHex_sum * 100, 0)))), end='%\n')

        print('{:-<40s}'.format(''), end='\n')
        print("blocks searched = " + str(versionHex_sum) + " blocks", end='\n \n')


def main():
    Coin.buildfiles()
    Coin.showstat()


if __name__ == "__main__":
    main()
