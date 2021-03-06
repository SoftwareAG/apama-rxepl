# Copyright (c) 2015-2018 Software AG, Darmstadt, Germany and/or Software AG USA Inc., Reston, VA, USA, and/or its subsidiaries and/or its affiliates and/or their licensors. 
#
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from pysys.constants import *
from pysys.basetest import BaseTest
from apama.correlator import CorrelatorHelper

class PySysTest(BaseTest):

	def execute(self):
		correlator = CorrelatorHelper(self, name='correlator')
		correlator.start(logfile='correlator.log', config=os.path.join(PROJECT.TEST_SUBJECT_DIR, 'initialization.yaml'))

		correlator.flush()
		correlator.injectEPL(filenames='testUtils.mon', filedir=PROJECT.UTILS_DIR)
		
		# Set the log level to DEBUG so that we can see when the listeners are killed
		correlator.setApplicationLogLevel(verbosity='DEBUG')
		
		# Start test results receiver
		correlator.receive(filename='TestResult.evt', channels=['TestResult'], logChannels=True)
		
		# Inject test
		correlator.injectEPL(filenames=['test.mon'])
		
		# wait for all events to be processed
		correlator.flush()
		
		# wait for test to complete
		self.waitForSignal('TestResult.evt', expr="TestComplete", condition="==1", timeout=10)
		
		# Output the engine_inspect result to a file to check for any remaining subscribed channels
		correlator.inspect(filename='preTerminateInspect.txt', arguments=['-x'])
		
		correlator.sendEventStrings('utils.KeepAliveUntilTerminated()')
		
		# Output the engine_inspect result to a file to check for non-terminated listeners
		correlator.inspect(filename='postTerminateInspect.txt', raw=True, arguments=['-x'])
		
	def validate(self):
		# check the main correlator log for Errors
		self.assertGrep('correlator.log', expr=' (ERROR|FATAL) ', contains=False)
		
		# Check that the test didn't fail
		self.assertGrep('TestResult.evt', expr='TestFailed', contains=False)
		
		# Check that there are no subscribed channels left
		self.assertGrep('preTerminateInspect.txt', expr='main\\s*\\d+\\s*\\d+\\s*(\\w+)', contains=False)
		
		# Check that there is nothing keeping the correlator alive
		self.assertDiff('postTerminateInspect.txt', 'terminatedEngineInspectReference.txt', filedir2=PROJECT.UTILS_DIR)

		
		# Check that the interval listener was killed
		self.assertLineCount('correlator.log', expr='Interval wait listener killed', condition='==1')
		