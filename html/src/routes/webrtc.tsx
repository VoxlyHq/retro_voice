/* eslint-disable  @typescript-eslint/no-explicit-any */

import { useEffect, useState, useRef } from 'react'

import { Card, CardHeader, CardTitle, CardContent, CardDescription, CardFooter } from '@/components/ui/card'
import { Checkbox } from '@/components/ui/checkbox'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectGroup, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'

interface InputDevice {
  id: string
  label: string
}

async function enumerateInputDevices(): Promise<InputDevice[]> {
  let mediaDevices: MediaDeviceInfo[] = []

  try {
    mediaDevices = await navigator.mediaDevices.enumerateDevices()
  } catch (e) {
    alert(e)
  }

  let counter = 0
  return mediaDevices
    .filter((device) => device.kind == 'videoinput')
    .map((device) => {
      counter += 1
      return {
        id: device.deviceId,
        label: device.label || 'Device #' + counter,
      }
    })
}

function sdpFilterCodec(kind: string, codec: string, realSdp: string) {
  const allowed = []
  // eslint-disable-next-line no-control-regex
  const rtxRegex = new RegExp('a=fmtp:(\\d+) apt=(\\d+)\r$')
  const codecRegex = new RegExp('a=rtpmap:([0-9]+) ' + escapeRegExp(codec))
  const videoRegex = new RegExp('(m=' + kind + ' .*?)( ([0-9]+))*\\s*$')

  const lines = realSdp.split('\n')

  let isKind = false
  for (let i = 0; i < lines.length; i++) {
    if (lines[i].startsWith('m=' + kind + ' ')) {
      isKind = true
    } else if (lines[i].startsWith('m=')) {
      isKind = false
    }

    if (isKind) {
      let match = lines[i].match(codecRegex)
      if (match) {
        allowed.push(parseInt(match[1]))
      }

      match = lines[i].match(rtxRegex)
      if (match && allowed.includes(parseInt(match[2]))) {
        allowed.push(parseInt(match[1]))
      }
    }
  }

  const skipRegex = 'a=(fmtp|rtcp-fb|rtpmap):([0-9]+)'
  let sdp = ''

  isKind = false
  for (let i = 0; i < lines.length; i++) {
    if (lines[i].startsWith('m=' + kind + ' ')) {
      isKind = true
    } else if (lines[i].startsWith('m=')) {
      isKind = false
    }

    if (isKind) {
      const skipMatch = lines[i].match(skipRegex)
      if (skipMatch && !allowed.includes(parseInt(skipMatch[2]))) {
        continue
      } else if (lines[i].match(videoRegex)) {
        sdp += lines[i].replace(videoRegex, '$1 ' + allowed.join(' ')) + '\n'
      } else {
        sdp += lines[i] + '\n'
      }
    } else {
      sdp += lines[i] + '\n'
    }
  }

  return sdp
}

function escapeRegExp(str: string) {
  return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') // $& means the whole matched string
}

export function WebRTCPage() {
  const [videoInputs, setVideoInputs] = useState<InputDevice[]>([])
  const [videoDevice, setVideoDevice] = useState('default')
  const [videoRes, setVideoRes] = useState('default')
  const [videoTransform, setVideoTransform] = useState('none')
  const [videoCodec, setVideoCodec] = useState('H264/90000')
  const [isSTUNEnabled, setIsSTUNEnabled] = useState(false)
  const [canStartWebcam, setCanStartWebcam] = useState(true)
  const [canStartScreenshare, setCanStartScreenshare] = useState(true)
  const [canStop, setCanStop] = useState(false)
  const [isMediaVisible, setIsMediaVisible] = useState(false)
  const videoRef = useRef<HTMLVideoElement>(null)
  const [iceGatheringState, setIceGatheringState] = useState('')
  const [iceConnectionState, setIceConnectionState] = useState('')
  const [signalingState, setSignalingState] = useState('')
  const [offerSDP, setOfferSDP] = useState('')
  const [answerSDP, setAnswerSDP] = useState('')
  const [outboundCodec, setOutboundCodec] = useState('')
  const [outboundFps, setOutboundFps] = useState(0)
  const [outboundWidth, setOutboundWidth] = useState(0)
  const [outboundHeight, setOutboundHeight] = useState(0)
  const [inboundCodec, setInboundCodec] = useState('')
  const [inboundFps, setInboundFps] = useState('')
  const [inboundWidth, setInboundWidth] = useState(0)
  const [inboundHeight, setInboundHeight] = useState(0)
  const pcRef = useRef<RTCPeerConnection | null>(null)
  const statsTimerRef = useRef<number | null>(null)

  function createPeerConnection() {
    const config: any = {
      sdpSemantics: 'unified-plan',
    }

    if (isSTUNEnabled) {
      config.iceServers = [{ urls: ['stun:stun.l.google.com:19302'] }]
    }

    const pc = new RTCPeerConnection(config)

    setIceGatheringState(pc.iceGatheringState)
    setIceConnectionState(pc.iceConnectionState)
    setSignalingState(pc.signalingState)

    pc.addEventListener(
      'icegatheringstatechange',
      () => {
        setIceGatheringState((prevState) => prevState + ' -> ' + pc.iceGatheringState)
      },
      false
    )

    pc.addEventListener(
      'iceconnectionstatechange',
      () => {
        setIceConnectionState((prevState) => prevState + ' -> ' + pc.iceConnectionState)
      },
      false
    )

    pc.addEventListener(
      'signalingstatechange',
      () => {
        setSignalingState((prevState) => prevState + ' -> ' + pc.signalingState)
      },
      false
    )

    // connect audio / video
    pc.addEventListener('track', (evt) => {
      if (evt.track.kind == 'video' && videoRef.current) {
        videoRef.current.srcObject = evt.streams[0]
      }
    })

    return pc
  }

  function startGatheringStats() {
    if (statsTimerRef.current) {
      window.clearInterval(statsTimerRef.current)
    }
    statsTimerRef.current = window.setInterval(async () => {
      if (pcRef.current) {
        const stats = await pcRef.current.getStats()
        stats.forEach((stat) => {
          if (stat.type === 'outbound-rtp' && stat.kind === 'video') {
            const codec = stats.get(stat.codecId)
            setOutboundCodec(codec ? codec.mimeType : 'N/A')
            setOutboundFps(stat.framesPerSecond || 0)
            setOutboundWidth(stat.frameWidth)
            setOutboundHeight(stat.frameHeight)
          } else if (stat.type === 'inbound-rtp' && stat.kind === 'video') {
            const codec = stats.get(stat.codecId)
            setInboundCodec(codec ? codec.mimeType : 'N/A')
            setInboundFps(stat.framesPerSecond || 0)
            setInboundWidth(stat.frameWidth)
            setInboundHeight(stat.frameHeight)
          }
        })
      }
    }, 1000)
  }

  async function negotiate(): Promise<void> {
    const pc = pcRef.current!
    const initialOffer = await pc.createOffer()
    pc.setLocalDescription(initialOffer)

    // wait for ICE gathering to complete
    if (pc.iceGatheringState !== 'complete') {
      await new Promise<void>((resolve) => {
        function checkState() {
          if (pc.iceGatheringState === 'complete') {
            pc.removeEventListener('icegatheringstatechange', checkState)
            resolve()
          }
        }
        pc.addEventListener('icegatheringstatechange', checkState)
      })
    }

    const offer = pc.localDescription!
    if (videoCodec !== 'default') {
      // @ts-expect-error: According to WebRTC spec the sdp field is probably read-only,
      // but this still works in Chrome/Firefox for the time being
      offer.sdp = sdpFilterCodec('video', videoCodec, offer.sdp)
    }

    setOfferSDP(offer.sdp)
    const response = await fetch(`${__BASE_API_URL__}/offer`, {
      body: JSON.stringify({
        sdp: offer.sdp,
        type: offer.type,
        video_transform: videoTransform,
      }),
      headers: {
        'Content-Type': 'application/json',
      },
      method: 'POST',
    })

    const answer = await response.json()
    if (response.ok) {
      setAnswerSDP(answer.sdp)
      pc.setRemoteDescription(answer)
    } else if (answer.error) {
      alert(answer.error)
    }
  }

  const onStartWebcam = async () => {
    setCanStartWebcam(false)
    setCanStartScreenshare(false)

    pcRef.current = createPeerConnection()

    // Build media constraints.
    const constraints = {
      audio: false,
      video: false,
    }

    const videoConstraints: any = {}

    if (videoDevice && videoDevice !== 'default') {
      videoConstraints.deviceId = { exact: videoDevice }
    }

    if (videoRes && videoRes !== 'default') {
      const dimensions = videoRes.split('x')
      videoConstraints.width = parseInt(dimensions[0], 0)
      videoConstraints.height = parseInt(dimensions[1], 0)
    }

    constraints.video = Object.keys(videoConstraints).length ? videoConstraints : true

    // get stream and start negotiation
    try {
      const stream = await navigator.mediaDevices.getUserMedia(constraints)
      stream.getTracks().forEach((track) => {
        pcRef.current!.addTrack(track, stream)
      })
    } catch (err) {
      alert('Could not acquire media: ' + err)
    }

    setIsMediaVisible(true)
    await negotiate()
    startGatheringStats()

    setCanStop(true)
  }

  const onStartScreenshare = async () => {
    setCanStartWebcam(false)
    setCanStartScreenshare(false)

    pcRef.current = createPeerConnection()

    // Build media constraints.
    const constraints: MediaStreamConstraints = {
      audio: false,
      video: false,
    }

    // TODO: Chrome supports some additional constraints that control what's
    // selected by default on the Chrome screenshare dialog, we don't bother
    // setting any of them here though.
    // See https://developer.chrome.com/docs/web-platform/screen-sharing-controls/
    const videoConstraints: MediaTrackConstraints = {}
    constraints.video = Object.keys(videoConstraints).length ? videoConstraints : true

    // get stream and start negotiation
    try {
      const stream = await navigator.mediaDevices.getDisplayMedia(constraints)
      const tracks = stream.getVideoTracks()
      if (tracks.length > 0) {
        // this should fire whenever the user stops sharing via the browser UI
        tracks[0].addEventListener('ended', () => {
          onStop()
        })
      }
      stream.getTracks().forEach((track) => {
        pcRef.current!.addTrack(track, stream)
      })
    } catch (err) {
      alert('Could not acquire media: ' + err)
    }

    setIsMediaVisible(true)
    await negotiate()
    startGatheringStats()

    setCanStop(true)
  }

  const onStop = () => {
    const pc = pcRef.current!
    setCanStop(false)

    if (statsTimerRef.current) {
      window.clearInterval(statsTimerRef.current)
      statsTimerRef.current = null
    }

    // close transceivers
    if (pc.getTransceivers) {
      pc.getTransceivers().forEach((transceiver: any) => {
        if (transceiver.stop) {
          transceiver.stop()
        }
      })
    }

    // close local audio / video
    pc.getSenders().forEach((sender: any) => {
      sender.track.stop()
    })

    // close peer connection
    setTimeout(() => {
      pc.close()

      setCanStartWebcam(true)
      setCanStartScreenshare(true)
    }, 500)
  }

  useEffect(() => {
    ;(async () => {
      const devices = await enumerateInputDevices()
      setVideoInputs(devices)
    })()
  }, [])

  return (
    <div className="space-y-4 my-4">
      <Card className="max-w-4xl mx-auto">
        <CardHeader>
          <CardTitle className="text-xl">Options</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex space-x-2">
            <Select onValueChange={setVideoDevice}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Default device" />
              </SelectTrigger>
              <SelectContent>
                <SelectGroup>
                  {videoInputs.map((device) => (
                    <SelectItem key={device.id} value={device.id}>
                      {device.label}
                    </SelectItem>
                  ))}
                </SelectGroup>
              </SelectContent>
            </Select>
            <Select onValueChange={setVideoRes}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Default resolution" />
              </SelectTrigger>
              <SelectContent>
                <SelectGroup>
                  <SelectItem value="default">Default resolution</SelectItem>
                  <SelectItem value="320x240">320x240</SelectItem>
                  <SelectItem value="640x480">640x480</SelectItem>
                  <SelectItem value="960x540">960x540</SelectItem>
                  <SelectItem value="1280x720">1280x720</SelectItem>
                </SelectGroup>
              </SelectContent>
            </Select>
            <Select onValueChange={setVideoTransform}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="No transform" />
              </SelectTrigger>
              <SelectContent>
                <SelectGroup>
                  <SelectItem value="none">No transform</SelectItem>
                  <SelectItem value="edges">Edge detection</SelectItem>
                  <SelectItem value="cartoon">Cartoon effect</SelectItem>
                  <SelectItem value="rotate">Rotate</SelectItem>
                </SelectGroup>
              </SelectContent>
            </Select>
            <Select value={videoCodec} onValueChange={setVideoCodec}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Default codecs" />
              </SelectTrigger>
              <SelectContent>
                <SelectGroup>
                  <SelectItem value="default">Default codecs</SelectItem>
                  <SelectItem value="VP8/90000">VP8</SelectItem>
                  <SelectItem value="H264/90000">H264</SelectItem>
                </SelectGroup>
              </SelectContent>
            </Select>
          </div>

          <div className="flex items-center space-x-2">
            <Checkbox id="use-stun" checked={isSTUNEnabled} onCheckedChange={(value) => setIsSTUNEnabled(!!value)} />
            <label
              htmlFor="use-stun"
              className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
            >
              Use STUN/TURN server
            </label>
          </div>
        </CardContent>
      </Card>
      <Card className="max-w-fit mx-auto">
        <CardHeader>
          <CardTitle className="text-xl">State</CardTitle>
          <CardDescription>
            <p>
              ICE gathering state: <span>{iceGatheringState}</span>
            </p>
            <p>
              ICE connection state: <span>{iceConnectionState}</span>
            </p>
            <p>
              Signaling state: <span>{signalingState}</span>
            </p>
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isMediaVisible && (
            <div className="flex space-x-8">
              <div>
                <h3 className="text-lg">Outbound Stats</h3>
                <pre>
                  {outboundCodec}@{outboundWidth}x{outboundHeight}
                </pre>
                <pre>{outboundFps} fps</pre>
              </div>
              <div>
                <h3 className="text-lg">Inbound Stats</h3>
                <pre>
                  {inboundCodec}@{inboundWidth}x{inboundHeight}
                </pre>
                <pre>{inboundFps} fps</pre>
              </div>
            </div>
          )}
          <div id="media" style={{ display: isMediaVisible ? 'block' : 'none' }}>
            <video id="video" ref={videoRef} autoPlay playsInline></video>
          </div>
          <CardFooter className="space-x-2 my-2 p-0">
            <Button onClick={onStartWebcam} disabled={!canStartWebcam}>
              Start Webcam
            </Button>
            <Button onClick={onStartScreenshare} disabled={!canStartScreenshare}>
              Start Screenshare
            </Button>
            <Button onClick={onStop} disabled={!canStop}>
              Stop
            </Button>
          </CardFooter>
        </CardContent>
      </Card>
      {(offerSDP || answerSDP) && (
        <Card className="max-w-fit mx-auto">
          <CardHeader>
            <CardTitle className="text-xl">SDP</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <h3 className="text-xl">Offer</h3>
            <pre>{offerSDP}</pre>

            <h3 className="text-xl">Answer</h3>
            <pre>{answerSDP}</pre>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
