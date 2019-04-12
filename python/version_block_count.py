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
    def buildfiles(cls, start_block=0, block_amount=False):
        cls.checkmnsync()
        stop_block = 0
        block_json = {}

        if start_block == 0:
            start_block = cls.currentblock(start_block)

        if block_amount == False:
            stop_block = start_block - 999
        else:
            stop_block = start_block - block_amount

        if cls.openfile(cls.blocks_tmp):
            block_json = cls.openfile(cls.blocks_tmp)
            _last_key = int(sorted(block_json.keys())[-1])

            if _last_key != start_block and _last_key != 0:
                stop_block = _last_key
            else:
                stop_block = start_block

        if start_block != stop_block:
            print('\033[33;5mWait till download is done!\033[0m')
            while stop_block <=start_block:
                blockhash = cls.clicmd('getblockhash ' + str(stop_block), 'string')
                fullblock = cls.clicmd('getblock "'+blockhash+'" ')
                block_json[str(stop_block)] = fullblock
                #print(fullblock)
                stop_block = int(stop_block) + 1

            # cursor up one line
            sys.stdout.write('\x1b[1A')
            # delete last line
            sys.stdout.write('\x1b[2K')

            cp_block_json = block_json.copy()
            for i in block_json:
                if int(i) < int(start_block) - 999:
                    del cp_block_json[i]

            cls.writefile(cls.blocks_tmp, cp_block_json)

    @classmethod
    def showstat(cls, blockcount=1000):
        def summation(collection):
            sum = 0
            for i in collection:
                sum = sum + collection[i]
            return sum

        stat_dict = cls.openfile(cls.blocks_tmp)
        _last_key = sorted(stat_dict.keys())[-1]

        version_name = {'20000000': '20000000 old VersionBlock',
                        '20000008': '20000008 GN VersionBlock'}


        versionHex_list = []
        for i in stat_dict:
            versionHex_list.append(stat_dict[i]['versionHex'])

        count_versionHex = collections.Counter(versionHex_list)
        versionHex_sum = summation(count_versionHex)
        print(' ')
        print('{:<40s}'.format('MINED_BLOCKS [ blockheight = '+_last_key+']'), end='\n')
        print('{:=<40s}'.format(''), end='\n')

        for i in count_versionHex:

            if i in version_name:
                v_name = version_name[i]
            else:
                v_name = i + ' xxxx'

            print('{:<25s}'.format(v_name), end=': ')
            print('{:>5s}'.format(str(count_versionHex[i])), end=' ')
            print('{:>5s}'.format(str(int(round(count_versionHex[i]/versionHex_sum*100, 0)))), end='%\n')

        print('{:-<40s}'.format(''), end='\n')
        print("blocks searched = "+str(versionHex_sum)+" blocks")




def main():
    Coin.buildfiles()
    Coin.showstat()


if __name__ == "__main__":
    main()
