import telnetlib3, asyncio

async def here(reader, writer):
#  writer.write("a"*80)
  for n in list(range(32)) + [int("7f", 16)]:
    if n not in (8, 9, 10, 12, 13):
#      await reader.read(1)
      writer.write(f"{n:02x} " +chr(n) +"\x09")
      await writer.drain()
#  writer.write("\x1b[1mtest\x1b[22mtest\x1b[5mtest\x1b[25mtest")
#  writer.write("\x1b[101mtest")
#  writer.write("\x1b[0 q")
#  writer.write("\x1b[?25l")
#  writer.write("\x1b[32mTest\x1b[27mTest\x1b[1;32;5mTest\x1b[27mTest")
#  writer.write("\x07")

  await asyncio.sleep(float('inf'))
 
async def main():
  server = await telnetlib3.create_server(host="localhost", port=23, shell=here)
  await server.wait_closed()

asyncio.run(main())

