import os
import time
from enum import Enum

#import fluidsynth

import mido
from mido import Message, MetaMessage, MidiFile, MidiTrack



#00 - End Of Track
#01 xx - Set Instrument
#02 xx yy - Set L/R Volume
#03 xx yy - Jump
#04 xx yy zz - Call/Repeat Subroutine
#05 - End Subroutine
#06 xx (yy) - Default Duration On
#07 - Default Duration Off
#08 xx yy zz ww vv - Pitch Slide Up
#09 xx yy zz ww vv - Pitch Slide Down
#0A - Pitch Slide Off
#0B xx - Set Tempo
#0C xx - Add Tempo
#0D xx yy zz - Vibrato (No Delay)
#0E - Vibrato Off
#0F xx yy zz ww - Vibrato
#10 xx yy - Set ADSR Envelope
#11 xx yy - Master Volume L/R
#12 xx - Tuning
#13 xx - Transpose (Fine Tune)
#14 xx - Transpose (Relative)
#15 xx yy zz - Echo Param
#16 - Echo On
#17 - Echo Off
#18 xx xx xx xx xx xx xx xx - Echo Filter
#19 xx - Noise Frequency
#1A - Noise On
#1B - Noise Off
#1C xx - Set Variable Note 1
#1D xx - Set Variable Note 2

#26 xx yy zz ww - Pitch Slide Down (Simpler)
#27 xx yy zz ww - Pitch Slide Up (Simpler)

#2B - Long Duration On
#2C - Long Duration Off

class Command(Enum):
	# COMMON RAREWARE COMMANDS
	END_TRACK = 0x00
	SET_INSTRUMENT = 0x01
	SET_STEREO_VOLUME = 0x02
	JUMP = 0x03
	REPEAT_SUB_SEQUENCE = 0x04
	RETURN = 0x05
	DEFAULT_DURATION_ON = 0x06
	DEFAULT_DURATION_OFF = 0x07
	PITCH_SLIDE_UP = 0x08
	PITCH_SLIDE_DOWN = 0x09
	PITCH_SLIDE_OFF = 0x0A
	SET_TEMPO = 0x0B
	INCREASE_TEMPO = 0x0C
	VIBRATO_NO_DELAY_ON = 0x0D
	VIBRATO_OFF = 0x0E
	VIBRATO_ON = 0x0F
	SET_ADSR = 0x10
	SET_STEREO_MASTER_VOLUME = 0x11
	SET_TUNE = 0x12
	SET_PITCH = 0x13
	SET_PITCH_RELATIVE = 0x14
	SET_ECHO = 0x15
	ECHO_ON = 0x16
	ECHO_OFF = 0x17
	SET_ECHO_FILTER = 0x18
	SET_NOISE = 0x19
	NOISE_ON = 0x1A
	NOISE_OFF = 0x1B
	SET_VARIABLE_NOTE_1 = 0x1C
	SET_VARIABLE_NOTE_2 = 0x1D

	# GAME SPECIFIC
	SET_ECHO_DELAY = 0x1F

	# DKC 2 COMMANDS
	CALL_SUB_SEQUENCE = 0x21

	# DKC 2 COMMANDS
	SET_MONO_VOLUME = 0x23

	# COMMON RAREWARE COMMANDS
	PITCH_SLIDE_SIMPLE_UP = 0x26
	PITCH_SLIDE_SIMPLE_DOWN = 0x27

	# DKC 2 COMMANDS
	LONG_DURATION_ON = 0x2B
	LONG_DURATION_OFF = 0x2C



def read_byte(data, address):
	byte = int.from_bytes(data[address:address+1], byteorder='big')
	return byte


def read_word_little_endian(data, address):
	word = int.from_bytes(data[address:address+2], byteorder='little')
	return word


def read_word_big_endian(data, address):
	word = int.from_bytes(data[address:address+2], byteorder='big')
	return word


def get_data_chunk(data, address_a, address_b):
	chunk = data[address_a:address_b]
	return chunk


# Convert SNES HiROM address to raw ROM file address
def snes_to_rom_address(address):
	address &= 0x3FFFFF
	return address


def load_file(path):
	try:
		file = open(path, 'rb')
		while True:
			data = file.read(-1)  
			if not data:
				break
			return bytes(data)
	except IOError:
		print('ERROR: Failed to open file.')
		return bytes()


def save_file(path, address, data):
	try:
		file = open(path, 'wb')
		if True:
			file.seek(address)
			file.write(data)
			return
	except IOError:
		print('ERROR: Failed to open file.')
		return


def snes_to_midi_ticks(snes_ticks):
	return snes_ticks * (480 / TPQN)


# TODO: this code is probably bad, it basically tries to get the volume differential between left and right from the SNES and apply that as panning
def set_volume_and_panning(volume_left, volume_right):
	pan_direction = ((volume_right - volume_left) // 4) + 63
	volume = max(volume_left, volume_right) // 2
	volume = max(0, min(volume * 4, 127))
	track.append(Message('control_change', channel=0, control=10, value=pan_direction))
	#track.append(Message('control_change', channel=channel, control=7, value=volume))


def rest_note(duration, channel):
	# Write the rest note to the MIDI
	track.append(Message('note_on', channel=0, note=0, velocity=0, time=0))
	track.append(Message('note_off', channel=0, note=0, velocity=127, time=int(snes_to_midi_ticks(duration))))
#	time.sleep(duration / (tempo / 3.0))


def play_note(note, duration, channel, volume):
	# Subtract from the SNES note number to align it with the MIDI note table
	midi_note = note - 93
	
	# Write the note to the MIDI
	track.append(Message('note_on', channel=0, note=midi_note, velocity=max(0, min(volume * 4, 127)), time=0))
	track.append(Message('note_off', channel=0, note=midi_note, velocity=127, time=int(snes_to_midi_ticks(duration))))

#	fs.noteon(0, midi_note, 100)
#	time.sleep(duration / (tempo / 3.0))
#	fs.noteoff(0, 60)


def log_command(text):
	if log_command_output:
		print(text)



# WIP dictionary for tracking and writing specific instruments to different MIDI tracks
#track_dictionary = {}
#track_count = 0
#current_track_number = 0
#
#current_track_number = track_dictionary.get(instrument)
#
#if not current_track_number:
#	track_count += 1
#	track_dictionary.update({instrument: track_count})
#	current_track_number = track_count


log_command_output = False

if __name__ == '__main__':
	# Read ROM data
	rom_data = load_file('DREAM.sfc')

	# Tempo calculation constants
	TPQN = 32
	timer_0_divider = 100
	
	#track_rom_address = snes_to_rom_address(0xC2119F)
	#track_rom_address = snes_to_rom_address(0xC2223C)
	#track_rom_address = snes_to_rom_address(0xC22C2F)
	
	# Define the list of all the song addresses in ROM
	track_addresses = [
		snes_to_rom_address(0xC2119F),	# Level 1
		snes_to_rom_address(0xC2223C),	# Title
		snes_to_rom_address(0xC22C2F)	# Ambience
	]
	
	track_names = [
		'Dream - Land of Giants: Level 1',
		'Dream - Land of Giants: Title',
		'Dream - Land of Giants: Ambience'
	]


	# Iterate over every song defined in the array and export them to MIDIs
	for song_number in range(len(track_addresses)):
	#for track_rom_address in track_addresses:
		track_rom_address = track_addresses[song_number]
		track_name = track_names[song_number]
		
		#Create MIDI file
		mid = MidiFile()
		
		# Get the ARAM base of the song
		track_data_base = read_word_little_endian(rom_data, track_rom_address)

		# Get the ARAM upload size of the song
		track_data_size = read_word_little_endian(rom_data, track_rom_address+2) * 2

		# Get the raw bytes of the song from ROM
		track_data = get_data_chunk(rom_data, track_rom_address + 4, track_rom_address + track_data_size+4)

		# Get the SNES tempo from the song header
		snes_tempo = read_byte(track_data, 0x10)

		# Calculate the true BPM
		bpm = 60000000.0 / (TPQN * (125 * timer_0_divider)) * (snes_tempo / 256.0)

		print('Exporting ' + track_name + ' from ROM address: ' + hex(track_rom_address) + ' at ' + str(bpm) + 'BPM')

		# Export all 8 channels to the MIDI file
		for channel in range(0, 8):
			print('	Exporting channel #' + str(channel+1))
			
			# Initialize a new MIDI track
			track = MidiTrack()
			mid.tracks.append(track)
			track.append(Message('program_change', program=0, time=0))
			
			# Set the tempo of the track
			tempo = mido.bpm2tempo(bpm)
			track.append(MetaMessage('set_tempo', tempo=tempo, time=0))
			
			# Read the pointer to the current channels data from the song header
			track_read_offset = read_word_little_endian(track_data, (channel * 2)) - track_data_base

			# Reset general channel attributes
			default_duration = 0
			long_duration = False
			echo = False
			vibrato = False
			
			instrument = 0
			master_volume_left = 0
			master_volume_right = 0
			volume_left = 0
			volume_right = 0
			variable_note_1 = 0
			variable_note_2 = 0
			
			# Initialize a sequence call stack so we can keep track of nested sequences calls and loops
			call_stack = []
			call_repeat_stack = []
			call_count_stack = []
			call_depth = 0

			#Setup fluidsynth for realtime output
#			fs = fluidsynth.Synth()
#			fs.start()
#
#			sfid = fs.sfload(
#			"/usr/share/sounds/sf2/FluidR3_GM.sf2"
#			)
#
#			fs.program_select(0, sfid, 0, 0)
			

			# Write a dummy note so the actual note data lines up with the 2nd measure
			track.append(Message('note_on', channel=channel, note=0, velocity=0, time=0))
			track.append(Message('note_off', channel=channel, note=0, velocity=127, time=1920-240))

			# Set a limit on how many notes to export to channel (since the songs can technically loop forever)
			note_count_cutoff = 2000

			# Loop through the track and parse commands
			while True:
				# If enough notes have been exported then save the MIDI and exit
				if note_count_cutoff <= 0:
					mid.save(track_name + '.mid')
					break

				# Read the audio command from ROM
				command = read_byte(track_data, track_read_offset)
				

				# Parse the command


				# COMMON RAREWARE COMMANDS
				if command == Command.END_TRACK.value:
					log_command('END_TRACK')
					break

				elif command == Command.SET_INSTRUMENT.value:
					log_command('SET_INSTRUMENT')
					instrument = read_byte(track_data, track_read_offset+1)
					track_read_offset += 2

				elif command == Command.SET_STEREO_VOLUME.value:
					log_command('SET_STEREO_VOLUME')
					volume_left = read_byte(track_data, track_read_offset+1)
					volume_right = read_byte(track_data, track_read_offset+2)
					set_volume_and_panning(volume_left, volume_right)
					track_read_offset += 3
				
				elif command == Command.JUMP.value:
					log_command('JUMP')
					track_read_offset = read_word_little_endian(track_data, track_read_offset+1) - track_data_base
				
				elif command == Command.REPEAT_SUB_SEQUENCE.value:
					log_command('REPEAT_SUB_SEQUENCE')
					call_stack.append(track_read_offset + 4)
					call_depth += 1
					call_count_stack.append(read_byte(track_data, track_read_offset+1))
					call_repeat_stack.append(read_word_little_endian(track_data, track_read_offset+2) - track_data_base)
					track_read_offset = read_word_little_endian(track_data, track_read_offset+2) - track_data_base
				
				elif command == Command.RETURN.value:
					log_command('RETURN')
					call_count = call_count_stack.pop()
					call_count -= 1
					if call_count <= 0:
						track_read_offset = call_stack.pop()
						call_repeat_stack.pop()
						call_depth -= 1
					else:
						track_read_offset = call_repeat_stack[-1]
						call_count_stack.append(call_count)
				
				elif command == Command.DEFAULT_DURATION_ON.value:
					log_command('DEFAULT_DURATION_ON')
					default_duration = read_byte(track_data, track_read_offset+1)
					track_read_offset += 1
				
				elif command == Command.DEFAULT_DURATION_OFF.value:
					log_command('DEFAULT_DURATION_OFF')
					default_duration = 0
					track_read_offset += 1
				
				elif command == Command.PITCH_SLIDE_UP.value:
					log_command('PITCH_SLIDE_UP')
					track_read_offset += 6
				
				elif command == Command.PITCH_SLIDE_DOWN.value:
					log_command('PITCH_SLIDE_DOWN')
					track_read_offset += 6
				
				elif command == Command.PITCH_SLIDE_OFF.value:
					log_command('PITCH_SLIDE_OFF')
					track_read_offset += 1
				
				elif command == Command.SET_TEMPO.value:
					log_command('SET_TEMPO')
					track_read_offset += 2
				
				elif command == Command.INCREASE_TEMPO.value:
					log_command('INCREASE_TEMPO')
					track_read_offset += 2
				
				elif command == Command.VIBRATO_NO_DELAY_ON.value:
					log_command('VIBRATO_NO_DELAY_ON')
					track_read_offset += 4
				
				elif command == Command.VIBRATO_OFF.value:
					log_command('VIBRATO_OFF')
					track_read_offset += 1
				
				elif command == Command.VIBRATO_ON.value:
					log_command('VIBRATO_ON')
					track_read_offset += 5
				
				elif command == Command.SET_ADSR.value:
					log_command('SET_ADSR')
					track_read_offset += 3
				
				elif command == Command.SET_STEREO_MASTER_VOLUME.value:
					log_command('SET_STEREO_MASTER_VOLUME')
					track_read_offset += 3
				
				elif command == Command.SET_TUNE.value:
					log_command('SET_TUNE')
					track_read_offset += 2
				
				elif command == Command.SET_PITCH.value:
					log_command('SET_PITCH')
					track_read_offset += 2
				
				elif command == Command.SET_PITCH_RELATIVE.value:
					log_command('SET_PITCH_RELATIVE')
					track_read_offset += 2
				
				elif command == Command.SET_ECHO.value:
					log_command('SET_ECHO')
					track_read_offset += 4
				
				elif command == Command.ECHO_ON.value:
					log_command('ECHO_ON')
					track_read_offset += 1
				
				elif command == Command.ECHO_OFF.value:
					log_command('ECHO_OFF')
					track_read_offset += 1
				
				elif command == Command.SET_ECHO_FILTER.value:
					log_command('SET_ECHO_FILTER')
					track_read_offset += 9
				
				elif command == Command.SET_NOISE.value:
					log_command('SET_NOISE')
					track_read_offset += 2
				
				elif command == Command.NOISE_ON.value:
					log_command('NOISE_ON')
					track_read_offset += 1
				
				elif command == Command.NOISE_OFF.value:
					log_command('NOISE_OFF')
					track_read_offset += 1
				
				elif command == Command.SET_VARIABLE_NOTE_1.value:
					log_command('SET_VARIABLE_NOTE_1')
					variable_note_1 = read_byte(track_data, track_read_offset+1)
					track_read_offset += 2
				
				elif command == Command.SET_VARIABLE_NOTE_2.value:
					log_command('SET_VARIABLE_NOTE_2')
					variable_note_2 = read_byte(track_data, track_read_offset+1)
					track_read_offset += 2

				elif command == Command.PITCH_SLIDE_SIMPLE_UP.value:
					log_command('PITCH_SLIDE_SIMPLE_UP')
					track_read_offset += 4
				
				elif command == Command.PITCH_SLIDE_SIMPLE_DOWN.value:
					log_command('PITCH_SLIDE_SIMPLE_DOWN')
					track_read_offset += 4

				elif command == Command.LONG_DURATION_ON.value:
					log_command('LONG_DURATION_ON')
					long_duration = True
					track_read_offset += 1
				
				elif command == Command.LONG_DURATION_OFF.value:
					log_command('LONG_DURATION_OFF')
					long_duration = False
					track_read_offset += 1


				# DKC 2 SPECIFIC COMMANDS
				elif command == Command.SET_ECHO_DELAY.value:
					log_command('SET_ECHO_DELAY')
					track_read_offset += 2
				
				elif command == Command.CALL_SUB_SEQUENCE.value:
					log_command('CALL_SUB_SEQUENCE')
					call_stack.append(track_read_offset + 3)
					call_depth += 1
					call_count_stack.append(1)
					call_repeat_stack.append(read_word_little_endian(track_data, track_read_offset+2) - track_data_base)
					track_read_offset = read_word_little_endian(track_data, track_read_offset+1) - track_data_base

				elif command == Command.SET_MONO_VOLUME.value:
					log_command('SET_MONO_VOLUME')
					volume = read_byte(track_data, track_read_offset+1)
					set_volume_and_panning(volume, volume)
					track_read_offset += 2


				# Note or unknown command
				elif command >= 0x80 and command <= 0xFF:
					# NOTE MATCH FOUND
					log_command('NOTE: ' + hex(command))
					
					# Handle different types of note duration
					if default_duration != 0:
						duration = default_duration
						track_read_offset += 1
					elif long_duration == True:
						duration = read_word_big_endian(track_data, track_read_offset+1)
						track_read_offset += 3
					else:
						duration = read_byte(track_data, track_read_offset+1)
						track_read_offset += 2
					
					# Decrement note limit counter
					note_count_cutoff -= 1

					# Handle rest notes and variable notes
					if command == 0x80:
						rest_note(duration, channel)
					
					elif command == 0xE0:
						play_note(variable_note_1, duration, channel, volume_left)
					
					elif command == 0xE1:
						play_note(variable_note_2, duration, channel, volume_left)
					
					else:
						play_note(command, duration, channel, volume_left)
				else:
					# ERROR NO COMMAND OR NOTE MATCH FOUND
					print('COMMAND NOT FOUND: ' + hex(command))

			mid.save(track_name + '.mid')
#			fs.delete()