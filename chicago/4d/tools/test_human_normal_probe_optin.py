import argparse,ast,contextlib,io,sys,unittest
from pathlib import Path
from types import SimpleNamespace
HERE=Path(__file__).parent
class OptIn(unittest.TestCase):
 def parse(self,args):
  tree=ast.parse((HERE/'human_teamster_blend.py').read_text());f=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='parse_args');ns={'argparse':argparse,'Path':Path,'ROOT':Path('/EXPLICIT_MOCK'),'sys':SimpleNamespace(argv=['fake','--']+args),'__doc__':'EXPLICIT MOCK parse'};exec(compile(ast.fix_missing_locations(ast.Module(body=[f],type_ignores=[])),'actual proposed parse_args','exec'),ns);return ns['parse_args']()
 def test_default_method_unchanged_and_explicit_tmp_optin(self):
  args=self.parse(['--variant','test','--output','/tmp/test.blend']);self.assertFalse(args.experimental_normal_probes)
  args=self.parse(['--variant','test','--output','/tmp/test.blend','--experimental-normal-probes','--normal-probe-receipts','/tmp/receipts']);self.assertTrue(args.experimental_normal_probes)
 def test_missing_conflicting_unsafe_receipt_args_refuse(self):
  common=['--variant','test','--output','/tmp/test.blend']
  for extra in [['--experimental-normal-probes'],['--normal-probe-receipts','/tmp/r'],['--experimental-normal-probes','--normal-probe-receipts','/workspace/r']]:
   with contextlib.redirect_stderr(io.StringIO()),self.assertRaises(SystemExit):self.parse(common+extra)
if __name__=='__main__':unittest.main()
